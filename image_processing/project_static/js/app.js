'use strict';


// Declare app level module which depends on filters, and services
angular.module('frontend', [
    'ngRoute',
    'djangoRESTResources',
    'flow',
    'frontend.controllers'
]).constant("AppConstant", {
    "API_URL": window.location.origin + "/api"
}).config(['flowFactoryProvider', 'AppConstant', '$httpProvider', function (flowFactoryProvider, AppConstant, $httpProvider) {
    flowFactoryProvider.defaults = {
        target: AppConstant.API_URL + '/document-upload/',
        permanentErrors: [404, 500, 501],
        maxChunkRetries: 1,
        chunkRetryInterval: 5000,
        simultaneousUploads: 4
    };
    $httpProvider.defaults.xsrfHeaderName = 'X-CSRFToken';
    $httpProvider.defaults.xsrfCookieName = 'csrftoken';
}]);
