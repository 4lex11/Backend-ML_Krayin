<?php
require 'C:/xampp/htdocs/KrayinCRM/laravel-crm-2.2/vendor/autoload.php';
$app=require 'C:/xampp/htdocs/KrayinCRM/laravel-crm-2.2/bootstrap/app.php';$app->make(Illuminate\Contracts\Console\Kernel::class)->bootstrap();
use Illuminate\Support\Facades\DB;
$result=[];
foreach(['persons','attribute_values','churn_sales_lines','churn_dataset_customers'] as $t){$rows=DB::table($t)->orderBy('id')->get();$result[$t]=['count'=>$rows->count(),'sha256'=>hash('sha256',json_encode($rows))];}
$result['predictions']=DB::table('churn_predictions')->count();
$result['pending_work']=DB::table('churn_work_items')->whereIn('status',['pending','running'])->count();
$result['qa_reviews']=DB::table('churn_reviews')->where('note','like','CRM061 QA %')->count();
$result['qa_accounts']=DB::table('users')->where('email','like','crm061-qa-%@example.invalid')->count();
$result['reviews']=DB::table('churn_reviews')->count();
$result['migrations']=DB::table('migrations')->where('migration','like','%churn%')->pluck('migration');
echo json_encode($result,JSON_PRETTY_PRINT|JSON_THROW_ON_ERROR);
