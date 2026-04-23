<?php
$url = "//{$_SERVER['HTTP_HOST']}{$_SERVER['REQUEST_URI']}";
$url_components = parse_url($url);
parse_str($url_components['query'] ?? '', $params);

if (!isset($params['memory'], $params['cpus'], $params['device-write'])) {
echo "Missing required params: memory, cpus, device-write";
exit;
}

$memory = escapeshellarg($params['memory']);
$cpus = escapeshellarg($params['cpus']);
$deviceWrite = escapeshellarg($params['device-write']);

$command = "sudo docker run --privileged -m {$memory} --memory-swap 1024m --cpus {$cpus} --device-write-bps /dev/nvme0n1:{$deviceWrite} --name myserver -d -p 80:80 server_image:1.0 2>&1";

$output = [];
$ret = 1;
exec($command, $output, $ret);

echo implode("\n", $output);
?>
