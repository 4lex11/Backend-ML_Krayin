<?php

// Test driver: credentials are read from configured files, never command arguments.
require $argv[1].'/vendor/autoload.php';
$app = require $argv[1].'/bootstrap/app.php';
$app->make(Illuminate\Contracts\Console\Kernel::class)->bootstrap();
try {
    $payload = json_decode(stream_get_contents(STDIN), true, 32, JSON_THROW_ON_ERROR);
    $result = $app->make(Webkul\Churn\Services\ChurnApiClient::class)->predictTransactions($payload);
    echo json_encode($result, JSON_THROW_ON_ERROR);
} catch (Webkul\Churn\Exceptions\ChurnApiException $error) {
    echo json_encode(['reason' => $error->reason, 'http_status' => $error->httpStatus, 'attempts' => $error->attempts]);
    exit(1);
}
