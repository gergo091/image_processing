'use strict';

/* Controllers */

angular.module('frontend.controllers', ['flow', 'djangoRESTResources']).
    controller('DetectionStatus', [
        '$scope',
        'djResource',
        '$location',
        'AppConstant',
        '$interval',
        function($scope, djResource, $location, AppConstant, $interval) {
            var api_root = AppConstant.API_URL;
            var DetectionRequestResource = djResource(api_root + "/detection-request/:id/:method/", {"id": "@id", "method": "@method"});

            var detection = null;
            var task_id = angular.element("#task_id").text();

            $scope.loading = true;

            DetectionRequestResource.query({"h": task_id}, function(data) {
                var stop = $interval(function() {
                    DetectionRequestResource.get(
                        {"id": data[0].id, "method": "get_status", "h": task_id},
                        function(d) {
                            $scope.loading = false;
                            $scope.detection = d;
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
            var DetectionRequestResource = djResource(api_root + "/detection-request/");
            var DetectionMethodResource = djResource(api_root + "/detection-method/");

            $scope.file_uploader = {};
            $scope.documents = {};
            $scope.documents_to_analyze = {};

            $scope.detection_methods = DetectionMethodResource.query();
            $scope.selected_methods = {};

            $scope.flowFileSuccess = function(file, message) {
                var data = angular.fromJson(message);
                $scope.documents[file.uniqueIdentifier] = data;
            }

            $scope.document_cancel = function(id) {
                delete $scope.documents[id];
            };

            $scope.start_detection = function() {
                // base checks
                if (!$scope.file_uploader.flow.files.length) {
                    alert("Upload some images first");
                    return;
                }
                var analyze_doc = [];
                angular.forEach($scope.documents, function(value, key) {
                    analyze_doc.push(parseInt(value.document));
                });
                var methods = [];
                angular.forEach($scope.selected_methods, function(v, k) {
                    methods.push(parseInt(k));
                });

                var request = new DetectionRequestResource({
                    "document_ids": analyze_doc,
                    "algorithm_ids": methods,
                });
                request.$save(function(data) {
                    window.location.href = "/detection-status/" + data.uid;
                });
            }
        }
    ]);
