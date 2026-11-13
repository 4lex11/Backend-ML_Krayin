<?php
// CRM-06.1 controlled driver: all writes are rolled back, including failure traces.
require $argv[1].'/vendor/autoload.php';
$app=require $argv[1].'/bootstrap/app.php';
$app->make(Illuminate\Contracts\Console\Kernel::class)->bootstrap();
use Illuminate\Support\Facades\DB;
use Webkul\Churn\Contracts\PanelRepository;
use Webkul\Churn\Contracts\PredictionRepository;
use Webkul\Churn\Contracts\WorkRepository;
use Webkul\Churn\Exceptions\ChurnApiException;
use Webkul\Churn\Services\CustomerInput;
use Webkul\Churn\Services\ChurnApiClient;
$counts=fn()=>['predictions'=>DB::table('churn_predictions')->count(),'runs'=>DB::table('churn_prediction_runs')->count(),'work'=>DB::table('churn_work_items')->count(),'reviews'=>DB::table('churn_reviews')->count()];
$before=$counts();
$customer=DB::table('churn_dataset_customers')->where('external_customer_id','AA-10315')->first();
$baseline=DB::table('churn_predictions')->where('dataset_customer_id',$customer->id)->get()->toJson();
if(DB::table('churn_work_items')->whereIn('status',['pending','running'])->exists()){throw new RuntimeException('Live pending work: cannot run isolated test');}
echo "READY\n";flush();
$mode=trim(fgets(STDIN));
$result=[];$failure=null;
DB::beginTransaction();
try {
 if($mode==='batch'){
  $repo=$app->make(WorkRepository::class);
  $queued=$repo->enqueue(null,'2018-06-30',null,null);
  $summary=$repo->process(1000);
  $expected=[];$file=fopen($argv[2],'r');$head=fgetcsv($file,0,',','"','');
  while(($row=fgetcsv($file,0,',','"',''))!==false){$r=array_combine($head,$row);$expected[$r['Customer ID']]=(float)$r['probabilidad_churn'];}fclose($file);
  $rows=DB::table('churn_predictions as p')->join('churn_dataset_customers as c','c.id','=','p.dataset_customer_id')->where('p.as_of','2018-06-30')->where('p.model_version','churn180-v1')->get(['p.*','c.external_customer_id']);
  $max=0.0;$limited=0;
  foreach($rows as $row){if(!array_key_exists($row->external_customer_id,$expected)){throw new RuntimeException('Unexpected predicted customer');}$max=max($max,abs($row->probability-$expected[$row->external_customer_id]));$limited+=(int)$row->limited_history;}
  $panel=$app->make(PanelRepository::class);
  $listing=$panel->listing(null,['q'=>'','risk'=>'','status'=>'','sort'=>'risk_desc','as_of'=>'2018-06-30']);
  $detail=$panel->detail($customer->id,null,'2018-06-30','churn180-v1');
  $passed=$queued['added']===793 && $summary===['completed'=>431,'error'=>0,'skipped'=>362] && count($rows)===431 && $max<1e-10 && $listing['summary']['saved']===431 && $listing['summary']['missing_count']===362 && $detail['inputMatches']===true && $detail['advice']==='limited';
  $result=['passed'=>$passed,'queued'=>$queued,'worker'=>$summary,'matched_clients'=>count($rows),'max_probability_error'=>$max,'limited_history_count'=>$limited,'panel_summary'=>$listing['summary'],'detail_verified'=>$detail['inputMatches'],'detail_advice'=>$detail['advice']];
 } else {
  $payload=$app->make(CustomerInput::class)->build($customer->id,'2018-06-30');
  if($mode==='invalid'){$payload['transactions'][0]['sales']=-1.0;}
  try {
   $saved=$app->make(PredictionRepository::class)->record($customer->id,$payload,fn($p)=>$app->make(ChurnApiClient::class)->predictTransactions($p));
   $result=['status'=>'success','created'=>$saved['created'],'probability'=>$saved['prediction']['probabilidad_churn']];
  } catch(ChurnApiException $e){$result=['status'=>'error','reason'=>$e->reason,'http_status'=>$e->httpStatus,'attempts'=>$e->attempts];}
  $run=DB::table('churn_prediction_runs')->where('dataset_customer_id',$customer->id)->orderByDesc('id')->first();
  $result['run_status']=$run->status;
  $result['valid_prediction_preserved']=$baseline===DB::table('churn_predictions')->where('dataset_customer_id',$customer->id)->get()->toJson();
  $detail=$app->make(PanelRepository::class)->detail($customer->id,null,'2018-06-30','churn180-v1');
  $result['panel_probability']=(float)$detail['prediction']->probability;
  $result['panel_latest_run']=$detail['runs'][0]->status;
 }
} catch(Throwable $e){$failure=get_class($e);}
finally {DB::rollBack();}
$result['rollback_verified']=$before===$counts() && $baseline===DB::table('churn_predictions')->where('dataset_customer_id',$customer->id)->get()->toJson();
if($failure){$result=['failure_type'=>$failure,'rollback_verified'=>$result['rollback_verified']];}
echo json_encode($result,JSON_THROW_ON_ERROR)."\n";
exit($failure?1:0);
