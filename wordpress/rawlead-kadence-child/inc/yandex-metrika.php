<?php
/**
 * Yandex.Metrika counter + helper script (O237).
 *
 * @package RawLead_Kadence_Child
 */

declare(strict_types=1);

if (!defined('ABSPATH')) {
    exit;
}

function rawlead_yandex_metrika_id(): string {
    if (defined('YANDEX_METRIKA_ID')) {
        return trim((string) YANDEX_METRIKA_ID);
    }
    $env = getenv('YANDEX_METRIKA_ID');
    return $env !== false ? trim((string) $env) : '';
}

function rawlead_yandex_metrika_enabled(): bool {
    $id = rawlead_yandex_metrika_id();
    if ($id === '' || !ctype_digit($id)) {
        return false;
    }
    if (rawlead_is_local_dev()) {
        return false;
    }
    $uri = (string) ($_SERVER['REQUEST_URI'] ?? '');
    if (str_starts_with($uri, '/ops/')) {
        return false;
    }
    return true;
}

function rawlead_yandex_metrika_print_head(): void {
    if (!rawlead_yandex_metrika_enabled()) {
        return;
    }
    $id = rawlead_yandex_metrika_id();
    ?>
<!-- Yandex.Metrika counter -->
<script type="text/javascript">
(function(m,e,t,r,i,k,a){m[i]=m[i]||function(){(m[i].a=m[i].a||[]).push(arguments)};
m[i].l=1*new Date();
for (var j = 0; j < document.scripts.length; j++) {if (document.scripts[j].src === r) { return; }}
k=e.createElement(t),a=e.getElementsByTagName(t)[0],k.async=1,k.src=r,a.parentNode.insertBefore(k,a)})
(window, document, "script", "https://mc.yandex.ru/metrika/tag.js", "ym");
ym(<?php echo (int) $id; ?>, "init", {
    clickmap: true,
    trackLinks: true,
    accurateTrackBounce: true,
    webvisor: true,
    ecommerce: "dataLayer",
    ssr: false
});
</script>
    <?php
}

function rawlead_yandex_metrika_print_noscript(): void {
    if (!rawlead_yandex_metrika_enabled()) {
        return;
    }
    $id = rawlead_yandex_metrika_id();
    printf(
        '<noscript><div><img src="https://mc.yandex.ru/watch/%1$s" style="position:absolute; left:-9999px;" alt="" /></div></noscript>' . "\n",
        esc_attr($id)
    );
}

add_action('wp_head', 'rawlead_yandex_metrika_print_head', 99);

add_action('wp_body_open', 'rawlead_yandex_metrika_print_noscript', 5);

add_action('wp_enqueue_scripts', static function (): void {
    if (!rawlead_yandex_metrika_enabled()) {
        return;
    }
    wp_enqueue_script(
        'rawlead-metrika',
        RAWLEAD_CHILD_URI . '/assets/js/rawlead-metrika.js',
        [],
        RAWLEAD_CHILD_VERSION,
        true
    );
    wp_localize_script('rawlead-metrika', 'rawleadMetrika', [
        'id' => (int) rawlead_yandex_metrika_id(),
    ]);
}, 15);
