import os
import datetime
from django.db import models
from django.core.files.storage import FileSystemStorage
from django.conf import settings
from django import forms
from django.core.files import File
from django.utils.encoding import force_str, force_text

# Create your models here.

class ChunkyUpload(models.Model):
    session_key = models.TextField(null=True)
    number = models.PositiveIntegerField()
    identifier = models.TextField()
    chunk = models.FileField(
        upload_to=u"chunks/%Y/%m/%d/%H/%M/%S/",
        null=True,
        blank=True,
        storage=FileSystemStorage(location=settings.DOCUMENTS_DIR),
    )


class Document(models.Model):
    image = models.ImageField(
        upload_to=u"docs/%Y/%m/%d/",
        null=True,
        blank=True,
        storage=FileSystemStorage(location=settings.DOCUMENTS_DIR),
    )
    name = models.TextField(null=True, blank=True)

    def __unicode__(self):
        return self.name


class TaskMethod(models.Model):
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=255)
    description = models.TextField(
        null=True,
        blank=True
    )

    def __unicode__(self):
        return self.name


class TaskRequest(models.Model):
    uid = models.TextField()
    task_id = models.TextField(
        blank=True,
        null=True
    )
    status = models.CharField(
        max_length="255",
        choices=(
            ("new", "New"),
            ("in_progress", "In progress"),
            ("completed", "Completed")
        ),
        default="new",
        blank=True,
    )

    created = models.DateTimeField(
        auto_now_add=True,
        editable=False
    )

    def is_completed(self):
        return self.status == "completed"

    def complete(self):
        self.status = "completed"
        self.save()

    @property
    def document_ids(self):
        return self.documents.values_list('id', flat=True)

    @document_ids.setter
    def document_ids(self, val):
        pass

    @property
    def algorithm_ids(self):
        pass

    @algorithm_ids.setter
    def algorithm_ids(self, val):
        pass


class TaskRequestLine(models.Model):
    task_request = models.ForeignKey(
        TaskRequest,
        related_name="lines"
    )
    task_id = models.TextField(
        blank=True,
        null=True
    )
    task_method = models.ForeignKey(TaskMethod)
    document = models.ForeignKey(
        Document,
        null=True,
        blank=True
    )
    status = models.CharField(
        max_length="255",
        choices=(
            ("new", "New"),
            ("in_progress", "In progress"),
            ("completed", "Completed")
        ),
        default="new",
        blank=True,
    )

    finished = models.DateTimeField(
        blank=True,
        null=True
    )

    created = models.DateTimeField(
        auto_now_add=True,
        editable=False
    )


    def _get_task(self):
        from apps.tasks import celery_app
        return celery_app.AsyncResult(self.task_id)

    def is_completed(self):
        return self.status == "completed"

    def complete(self, task=None):
        if task is None:
            task = self._get_task()

        result = TaskResult.objects.create(
            line=self,
            task_status=task.status
        )

        if isinstance(task.result, dict):
            if "filepath" in task.result:
                result.document = File(open(task.result["filepath"], "r"))

            if task.result.get("result_status", False):
                result.result_status = task.result["result_status"]

            result.result_note = task.result.get("result_note", None)

        result.save()

        self.status = "completed"
        self.save()

        return result


class TaskResult(models.Model):
    UPLOAD_TO = u"results/%Y/%m/%d/"

    line = models.ForeignKey(TaskRequestLine)
    document = models.FileField(
        upload_to=UPLOAD_TO,
        null=True,
        blank=True,
        storage=FileSystemStorage(location=settings.DOCUMENTS_DIR),
    )
    task_status = models.CharField(
        max_length="255",
        blank=True,
        null=True,
    )
    result_status = models.CharField(
        max_length="255",
        choices=(
            ("not_altered", "Not altered"),
            ("forgery", "Forgery"),
            ("unknow", "Unknow"),
        ),
        default="unknow",
        blank=True,
    )
    result_note = models.TextField(
        blank=True,
        null=True,
    )

    @classmethod
    def upload_to(cls):
        return os.path.join(
            settings.DOCUMENTS_DIR,
            os.path.normpath(
                force_text(
                    datetime.datetime.now().strftime(force_str(cls.UPLOAD_TO))
                )
            )
        )



class ChunkUploadForm(forms.ModelForm):
    class Meta:
        model = ChunkyUpload
        exclude = ("session_key", )
