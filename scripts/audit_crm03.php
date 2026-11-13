<?php

require $argv[1].'/vendor/autoload.php';
$app = require $argv[1].'/bootstrap/app.php';
$app->make(Illuminate\Contracts\Console\Kernel::class)->bootstrap();
use Illuminate\Support\Facades\DB;

$customer = DB::table('churn_dataset_customers')->where('source', 'superstore-sales')->where('external_customer_id', 'AA-10315')->first();
$result = [
    'predictions' => DB::table('churn_predictions')->where('dataset_customer_id', $customer->id)->where('as_of', '2018-06-30')->where('model_version', 'churn180-v1')->get(),
    'recent_runs' => DB::table('churn_prediction_runs')->where('dataset_customer_id', $customer->id)->orderByDesc('id')->limit(3)->get(),
];
echo json_encode($result, JSON_THROW_ON_ERROR);
