'use strict';

/* Controllers */

angular.module('frontend.controllers', ['flow', 'djangoRESTResources']).
    controller('TaskStatus', [
        '$scope',
        'djResource',
        '$location',
        'AppConstant',
        '$interval',
        function($scope, djResource, $location, AppConstant, $interval) {
            var api_root = AppConstant.API_URL;
            var TaskRequestResource = djResource(api_root + "/task-request/:id/:method/", {"id": "@id", "method": "@method"});

            var task = null;
            var task_id = angular.element("#task_id").text();

            $scope.loading = true;

            TaskRequestResource.query({"h": task_id}, function(data) {
                var stop = $interval(function() {
                    TaskRequestResource.get(
                        {"id": data[0].id, "method": "get_status", "h": task_id},
                        function(d) {
                            $scope.loading = false;
                            $scope.task = d;
                            if (d.status == "completed") {
                                $interval.cancel(stop);
                            }
                        }
                    )
                }, 5000);
            });
        }
    ]).
    controller('NewAnalyze', [
        '$scope',
        '$sce',
        'djResource',
        '$location',
        'AppConstant',
        '$window',
        function($scope, $sce, djResource, $location, AppConstant, $window) {
            var api_root = AppConstant.API_URL;
            var TaskRequestResource = djResource(api_root + "/task-request/");
            var TaskMethodResource = djResource(api_root + "/task-method/");

            $scope.file_uploader = {};
            $scope.documents = {};
            $scope.documents_to_analyze = {};

            $scope.task_methods = TaskMethodResource.query();
            $scope.selected_methods = {};

            $scope.flowFileSuccess = function(file, message) {
                var data = angular.fromJson(message);
                $scope.documents[file.uniqueIdentifier] = data;
            }

            $scope.document_cancel = function(id) {
                delete $scope.documents[id];
            };

            $scope.start_task = function() {
                // base checks
                if (!$scope.file_uploader.flow.files.length) {
                    alert("Upload some images first");
                    return;
                }
                var analyze_doc = [];
                angular.forEach($scope.documents, function(value, key) {
                    analyze_doc = parseInt(value.document);
                });
	
		var selected_method = $scope.selected_method;

                var request = new TaskRequestResource({
                    "document_id": analyze_doc,
                    "algorithm_id": selected_method,
                });
                request.$save(function(data) {
                    window.location.href = "/-status/" + data.uid;
                });
            }
        }
    ]);
