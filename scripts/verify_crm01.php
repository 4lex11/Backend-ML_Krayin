<?php

// Read-only verification. Usage: php verify_crm01.php <krayin-root> <train.csv>
if ($argc !== 3) {
    fwrite(STDERR, "Usage: php verify_crm01.php <krayin-root> <train.csv>\n");
    exit(1);
}
require $argv[1].'/vendor/autoload.php';
$app = require $argv[1].'/bootstrap/app.php';
$app->make(Illuminate\Contracts\Console\Kernel::class)->bootstrap();

use Illuminate\Support\Facades\DB;

$handle = fopen($argv[2], 'rb');
$header = fgetcsv($handle, 0, ',', '"', '');
$expected = [];
while (($values = fgetcsv($handle, 0, ',', '"', '')) !== false) {
    $raw = array_combine($header, $values);
    $expected[$raw['Row ID']] = $raw;
}
fclose($handle);
$lines = DB::table('churn_sales_lines as l')
    ->join('churn_dataset_customers as c', 'c.id', '=', 'l.dataset_customer_id')
    ->where('l.source', 'superstore-sales')
    ->get(['l.*', 'c.external_customer_id', 'c.dataset_name']);
$mismatches = 0;
foreach ($lines as $line) {
    $raw = $expected[$line->line_id] ?? null;
    if (! $raw) {
        $mismatches++;
        continue;
    }
    $date = DateTimeImmutable::createFromFormat('!d/m/Y', $raw['Order Date'])->format('Y-m-d');
    if ($line->external_customer_id !== $raw['Customer ID'] || $line->dataset_name !== $raw['Customer Name']
        || $line->order_id !== $raw['Order ID'] || $line->order_date !== $date
        || bccomp($line->sales, $raw['Sales'], 6) !== 0
        || $line->category !== $raw['Category'] || $line->subcategory !== $raw['Sub-Category']) {
        $mismatches++;
    }
    unset($expected[$line->line_id]);
}
$summary = DB::table('churn_sales_lines')->where('source', 'superstore-sales')
    ->selectRaw('count(*) as line_count, count(distinct order_id) as order_count, count(distinct line_id) as unique_lines, min(order_date) as first_date, max(order_date) as last_date, sum(sales) as sales_total')->first();
$customers = DB::table('churn_dataset_customers')->where('source', 'superstore-sales')->count();
$eligible = DB::table('churn_sales_lines')->where('source', 'superstore-sales')
    ->whereBetween('order_date', ['2018-01-01', '2018-06-30'])->distinct()->count('dataset_customer_id');
$result = [
    'dataset_sha256' => hash_file('sha256', $argv[2]),
    'database_version' => DB::selectOne('select version() as v')->v,
    'php_cli' => PHP_VERSION,
    'summary' => $summary,
    'mapped_customers' => $customers,
    'unique_persons' => DB::table('churn_dataset_customers')->distinct()->count('person_id'),
    'link_methods' => DB::table('churn_dataset_customers')->selectRaw('link_method, count(*) as n')->groupBy('link_method')->get(),
    'mismatched_rows' => $mismatches,
    'missing_rows' => count($expected),
    'eligible_at_2018_06_30' => $eligible,
    'dataset' => DB::table('churn_datasets')->where('source', 'superstore-sales')->first(),
    'migration_applied' => DB::table('migrations')->where('migration', '2026_10_28_000001_create_churn_dataset_tables')->exists(),
];
$result['passed'] = $mismatches === 0 && count($expected) === 0 && (int) $summary->line_count === 9800
    && (int) $summary->unique_lines === 9800 && (int) $summary->order_count === 4922 && $customers === 793
    && $result['unique_persons'] === 793 && $result['migration_applied'] && $eligible === 431;
echo json_encode($result, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE).PHP_EOL;
exit($result['passed'] ? 0 : 1);
