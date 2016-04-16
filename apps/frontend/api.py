# -*- coding: utf-8 -*-
# vim:fenc=utf-8

import os
import json
import uuid
from django.core.files.base import ContentFile
from django.conf import settings
from django.views import static
from rest_framework import status
from rest_framework.renderers import JSONRenderer
from rest_framework.decorators import detail_route
from rest_framework import viewsets
from rest_framework import serializers
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from drf_compound_fields.fields import ListField

from . models import (
    Document,
    ChunkyUpload,
    TaskRequest,
    TaskResult,
    TaskMethod,
    TaskRequestLine,
    ChunkUploadForm,
)
from .. tasks import process_line_task, celery_app
from .. import api_router as router

from celery import group




class ChunkyUploadSaver(object):

    def __init__(self, filename):
        self.filename = filename
        self.content_file = None

    def update_file(self, content):
        if self.content_file is None:
            self.content_file = ContentFile(
                content,
                name=self.filename,
            )
        else:
            self.content_file.write(content)


class TaskRequestSerializer(serializers.ModelSerializer):
    document_id = serializers.IntegerField(max_value=None, min_value=None)
    algorithm_id = serializers.IntegerField(max_value=None, min_value=None)
    status = serializers.CharField(read_only=True)
    uid = serializers.CharField(read_only=True, required=False)


    class Meta:
        model = TaskRequest


class TaskMethodSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskMethod


class TaskResultSerializer(serializers.ModelSerializer):
    document = serializers.SerializerMethodField('get_document_data')
    result_status = serializers.SerializerMethodField("get_status")

    def get_status(self, obj):
        return obj.get_result_status_display()

    def get_document_data(self, obj):
        if obj.document:
            return True
        return False


    class Meta:
        model = TaskResult


class TaskMethodViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = TaskMethod.objects.all()
    serializer_class = TaskMethodSerializer


class TaskRequestViewSet(viewsets.ModelViewSet):

    queryset = TaskRequest.objects.all()
    serializer_class = TaskRequestSerializer
    permission_classes = [AllowAny]

    def put(self, request):
        pass

    def create(self, request):
	print request.DATA
        return super(TaskRequestViewSet, self).create(request)

    def pre_save(self, obj):
        obj.uid = str(uuid.uuid4())

    def post_save(self, obj, created=False, data=None):
        if not created:
            return

        data = self.request.DATA if data is None else data

        # add documents
        docs = Document.objects.filter(
            id__in=[v for v in data['document_ids']]
        )
        # create lines for each document
        algs = TaskMethod.objects.filter(
            id__in=[v for v in data['algorithm_ids']]
        )

        for doc in docs:
            for alg in algs:
                TaskRequestLine.objects.create(
                    task_request=obj,
                    task_method=alg,
                    document=doc
                )

        #start tasks
        res = group(
            (process_line_task.s(
                method=line.task_method.code,
                filepath=line.document.image.file.name,
                upload_to=TaskResult.upload_to()
            ) for line in obj.lines.all())
        )()

        for index, line in enumerate(obj.lines.all()):
            line.task_id = res.children[index].id
            line.status = "in_progress"
            line.save()

        # update status
        obj.status = "in_progress"
        obj.task_id = res.id
        obj.save()


    def get_queryset(self, qs=None):
        qs = super(TaskRequestViewSet, self).get_queryset()
        if "h" in self.request.GET:
            return qs.filter(uid=self.request.GET.get("h"))
        else:
            return qs.none()

    @detail_route(methods=["get"])
    def get_doc(self, request, pk=None):
        obj = self.get_object()
        data = request.GET
        line = obj.lines.get(id=data.get("line"))
        results = line.taskresult_set.all()
        if not results.count():
            return Response(
                {"error": "No results for line."},
                status.HTTP_400_BAD_REQUEST,
            )

        # we except only one result for now
        result = results[0]

        return static.serve(
            request,
            os.path.relpath(
                result.document.path,
                settings.DOCUMENTS_DIR,
            ),
            document_root=settings.DOCUMENTS_DIR,
        )

    @detail_route(methods=["get"])
    def get_status(self, request, pk=None):
        obj = self.get_object()
        lines = []

        for line in obj.lines.all():
            result = None

            if line.is_completed():
                result = TaskResultSerializer(
                    line.taskresult_set.all()[0]
                ).data

            else:
                task = celery_app.AsyncResult(line.task_id)
                if task.ready():
                    # The task has been executed
                    result = TaskResultSerializer(line.complete(task)).data
                else:
                    result = {
                        "task_status": task.status        
                    }
            
            lines.append({
                "id": line.id,
                "document": line.document.name,
                "algorithm": line.task_method.name,
                "result": result
            })

        completed_lines = obj.lines.filter(status="completed").count()

        if not obj.is_completed() and completed_lines == obj.lines.count():
            obj.complete()

        return Response({
            "id": obj.id,
            "uid": obj.uid,
            "status": obj.status,
            "lines": lines,
            "progress": "%s / %s" % (completed_lines, obj.lines.count())
        })


class DocumentUploadViewset(viewsets.ViewSet):

    permission_classes = ()
    action_map = {
        "post": "create",
        "get": "list"
    }
    renderer_classes = (JSONRenderer, )

    def _prep_data(self, qd):
        return {
            "identifier": qd.get("flowIdentifier"),
            "number": qd.get("flowChunkNumber"),
        }

    def create(self, request, *args, **kwargs):
        session_key = request.session._session_key
        chunky_upload = ChunkUploadForm(self._prep_data(request.POST))
        if not chunky_upload.is_valid():
            return Response(
                json.loads(chunky_upload.errors.as_json()),
                status.HTTP_400_BAD_REQUEST,
            )
        chunky_data = chunky_upload.cleaned_data
        try:
            chunky_instance = ChunkyUpload.objects.get(
                session_key=session_key,
                identifier=chunky_data['identifier'],
                number=chunky_data["number"]
            )
        except ChunkyUpload.DoesNotExist:
            chunky_instance = chunky_upload.save(commit=False)
            chunky_instance.session_key = session_key
            chunky_instance.save()
            chunky_instance.chunk.save(
                u"{filename}-{number}".format(
                    filename=chunky_instance.identifier,
                    number=chunky_instance.number,
                ),
                request.FILES['file'],
            )

        _data = {
            "chunk": chunky_instance.id,
        }

        all_chunks = ChunkyUpload.objects.filter(
            session_key=session_key,
            identifier=chunky_data["identifier"]
        ).order_by("number")

        data = request.POST

        if int(data.get("flowTotalChunks")) == all_chunks.count():
            chunky_saver = ChunkyUploadSaver(data.get("flowFilename"))
            for chunk in all_chunks:
                chunky_saver.update_file(chunk.chunk.read())
            # delete all chunks
            all_chunks.delete()
            doc = Document.objects.create(name=data.get("flowFilename"))
            chunky_saver.content_file.open()
            doc.image.save(data.get("flowFilename"), chunky_saver.content_file)
            _data['document'] = doc.id
        
        return Response(_data)

    def list(self, request, *args, **kwargs):
        session_key = request.session._session_key
        chunky_upload = ChunkUploadForm(self._prep_data(request.GET))
        if not chunky_upload.is_valid():
            return Response(
                json.loads(chunky_upload.errors.as_json()),
                status.HTTP_400_BAD_REQUEST,
            )
        chunky_data = chunky_upload.cleaned_data
        try:
            chunky_instance = ChunkyUpload.objects.get(
                session_key=session_key,
                identifier=chunky_data['identifier'],
            )
        except ChunkyUpload.DoesNotExist:
            return Response(
                {"message": "Upload does not exist yet."},
                status.HTTP_404_NOT_FOUND,
            )

        return Response({
            "chunk": chunky_instance.id
        })



router.register(
    r'document-upload',
    DocumentUploadViewset,
    base_name="document_upload",
)

router.register(
    r'task-request',
    TaskRequestViewSet,
)

router.register(
    r'task-method',
    TaskMethodViewSet,
)
