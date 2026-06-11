<?php
/**
 * RawLead Kadence Child — enqueue, patterns, helpers.
 *
 * @package RawLead_Kadence_Child
 */

declare(strict_types=1);

if (!defined('ABSPATH')) {
    exit;
}

define('RAWLEAD_CHILD_VERSION', '1.18.56');
define('RAWLEAD_CHILD_DIR', get_stylesheet_directory());
define('RAWLEAD_CHILD_URI', get_stylesheet_directory_uri());

require_once RAWLEAD_CHILD_DIR . '/inc/template-tags.php';
require_once RAWLEAD_CHILD_DIR . '/inc/marketing.php';
require_once RAWLEAD_CHILD_DIR . '/inc/rawlead-api.php';

/**
 * Permalink for a skeleton page slug (home, how, pricing, …).
 */
function rawlead_page_url(string $slug): string {
    $page = get_page_by_path($slug, OBJECT, 'page');
    if ($page instanceof WP_Post) {
        return (string) get_permalink($page);
    }
    return home_url('/' . $slug . '/');
}

/**
 * Optional deep-link fallback URL for Telegram auth (without iframe widget).
 * return_to всегда подставляется из rawlead_cabinet_login_url() (prod / local).
 *
 * wp-config.php:
 *   define('RAWLEAD_TG_LOGIN_FALLBACK_URL', 'https://oauth.telegram.org/auth?...');
 */
function rawlead_tg_login_fallback_url(): string {
    $base = '';
    if (defined('RAWLEAD_TG_LOGIN_FALLBACK_URL')) {
        $base = trim((string) RAWLEAD_TG_LOGIN_FALLBACK_URL);
    } elseif (defined('RAWLEAD_TG_LOGIN_URL')) {
        $base = trim((string) RAWLEAD_TG_LOGIN_URL);
    }
    if ($base === '') {
        $bot_id = rawlead_tg_login_bot_id();
        if ($bot_id <= 0) {
            return '';
        }
        $base = 'https://oauth.telegram.org/auth?bot_id=' . $bot_id
            . '&origin=' . rawurlencode(home_url('/'));
    }
    return rawlead_tg_login_fallback_normalize($base);
}

function rawlead_tg_login_fallback_normalize(string $url): string {
    $parts = wp_parse_url($url);
    if (!is_array($parts) || empty($parts['host'])) {
        return $url;
    }
    $query = [];
    if (!empty($parts['query'])) {
        parse_str((string) $parts['query'], $query);
    }
    $query['return_to'] = rawlead_cabinet_login_url();
    $scheme = $parts['scheme'] ?? 'https';
    $path = $parts['path'] ?? '/auth';
    return $scheme . '://' . $parts['host'] . $path . '?' . http_build_query($query, '', '&', PHP_QUERY_RFC3986);
}

/**
 * Telegram Login bot id (preferred for JS popup fallback).
 */
function rawlead_tg_login_bot_id(): int {
    if (defined('RAWLEAD_TG_BOT_ID')) {
        return max(0, (int) RAWLEAD_TG_BOT_ID);
    }
    return 0;
}

add_action('after_setup_theme', static function (): void {
    add_theme_support('wp-block-styles');
    add_theme_support('responsive-embeds');
});

/** O96-Z1 / Z8 / Z9 — document title канон. */
add_filter('document_title_parts', static function (array $title): array {
    if (is_front_page()) {
        $title['title'] = 'RawLead — Заказы под твой стек';
        $title['tagline'] = '';
        $title['site'] = '';
    } elseif (is_page('pricing')) {
        $title['title'] = 'Тарифы — RawLead';
        $title['tagline'] = '';
        $title['site'] = '';
    } elseif (is_page('how')) {
        $title['title'] = 'Как работает — RawLead';
        $title['tagline'] = '';
        $title['site'] = '';
    }
    return $title;
});

/**
 * Brand favicon (RL mark) — overrides WP default site icon in browser tab.
 */
function rawlead_favicon_url(): string {
    return RAWLEAD_CHILD_URI . '/assets/images/rawlead-favicon-v1.png';
}

add_action('init', static function (): void {
    remove_action('wp_head', 'wp_site_icon', 99);
});

add_action('wp_head', static function (): void {
    $manrope_cyr = 'https://fonts.gstatic.com/s/manrope/v20/xn7_YHE41ni1AdIRqAuZuw1Bx9mbZk79FN_G-bnBeA.woff2';
    $manrope_lat = 'https://fonts.gstatic.com/s/manrope/v20/xn7_YHE41ni1AdIRqAuZuw1Bx9mbZk79FN_C-bk.woff2';
    printf(
        '<link rel="preload" href="%s" as="font" type="font/woff2" crossorigin>' . "\n",
        esc_url($manrope_cyr)
    );
    printf(
        '<link rel="preload" href="%s" as="font" type="font/woff2" crossorigin>' . "\n",
        esc_url($manrope_lat)
    );
    if (is_front_page()) {
        $unbounded_cyr = 'https://fonts.gstatic.com/s/unbounded/v12/Yq6F-LOTXCb04q32xlpat-6uR42XTqtG6__2447Ngc6L.woff2';
        printf(
            '<link rel="preload" href="%s" as="font" type="font/woff2" crossorigin>' . "\n",
            esc_url($unbounded_cyr)
        );
    }
}, 1);

add_action('wp_head', static function (): void {
    $icon = rawlead_favicon_url();
    printf(
        '<link rel="icon" type="image/png" href="%s" sizes="32x32">' . "\n",
        esc_url($icon)
    );
    printf(
        '<link rel="apple-touch-icon" href="%s">' . "\n",
        esc_url($icon)
    );
}, 99);

add_action('wp_enqueue_scripts', static function (): void {
    wp_enqueue_style(
        'rawlead-fonts',
        'https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700&family=Unbounded:wght@700;800;900&display=swap',
        [],
        null
    );

    wp_enqueue_style(
        'rawlead-kadence-child',
        get_stylesheet_uri(),
        ['rawlead-fonts'],
        RAWLEAD_CHILD_VERSION
    );

    wp_enqueue_style(
        'rawlead-tokens',
        RAWLEAD_CHILD_URI . '/assets/css/rawlead.css',
        ['rawlead-kadence-child'],
        RAWLEAD_CHILD_VERSION
    );

    if (is_front_page()) {
        wp_enqueue_script(
            'lenis',
            'https://cdn.jsdelivr.net/npm/lenis@1.1.18/dist/lenis.min.js',
            [],
            '1.1.18',
            true
        );
        wp_enqueue_script(
            'rawlead-scroll',
            RAWLEAD_CHILD_URI . '/assets/js/rawlead-scroll.js',
            ['lenis'],
            RAWLEAD_CHILD_VERSION,
            true
        );
        wp_localize_script('rawlead-scroll', 'rawleadHome', [
            'restFeed' => esc_url_raw(rest_url('rawlead/v1/feed')),
            'lentaUrl' => esc_url_raw(rawlead_page_url('lenta')),
        ]);
        wp_enqueue_script(
            'rawlead-flow',
            RAWLEAD_CHILD_URI . '/assets/js/rawlead-flow.js',
            [],
            RAWLEAD_CHILD_VERSION,
            true
        );
        wp_enqueue_script(
            'rawlead-ticker',
            RAWLEAD_CHILD_URI . '/assets/js/rawlead-ticker.js',
            [],
            RAWLEAD_CHILD_VERSION,
            true
        );
        wp_localize_script('rawlead-ticker', 'rawleadTicker', [
            'restStats' => esc_url_raw(rest_url('rawlead/v1/site-stats')),
        ]);
    }

    if (is_page('faq')) {
        wp_enqueue_script(
            'rawlead-faq',
            RAWLEAD_CHILD_URI . '/assets/js/rawlead-faq.js',
            [],
            RAWLEAD_CHILD_VERSION,
            true
        );
    }

    if (is_page('lenta')) {
        wp_enqueue_script(
            'rawlead-feed',
            RAWLEAD_CHILD_URI . '/assets/js/rawlead-feed.js',
            [],
            RAWLEAD_CHILD_VERSION,
            true
        );
        wp_localize_script('rawlead-feed', 'rawleadFeed', [
            'restFeed'         => esc_url_raw(rest_url('rawlead/v1/feed')),
            'restMeFeed'       => esc_url_raw(rest_url('rawlead/v1/me/feed')),
            'restFeedPrefs'    => esc_url_raw(rest_url('rawlead/v1/me/feed-prefs')),
            'restTags'         => esc_url_raw(rest_url('rawlead/v1/me/tags')),
            'restSkills'       => esc_url_raw(rest_url('rawlead/v1/skills/catalog')),
            'restDraft'        => esc_url_raw(rest_url('rawlead/v1/me/leads')),
            'restSubscription' => esc_url_raw(rest_url('rawlead/v1/me/subscription')),
            'pricingUrl'       => esc_url_raw(rawlead_page_url('pricing')),
            'cabinetUrl'       => esc_url_raw(rawlead_page_url('cabinet')),
            'botPayUrl'        => esc_url_raw('https://t.me/' . rawlead_tg_login_bot_username() . '?start=pay'),
            'nonce'            => wp_create_nonce('wp_rest'),
            'apiBase'          => rawlead_api_base_url(),
        ]);
    }

    if (is_page('cabinet')) {
        wp_enqueue_script(
            'rawlead-cabinet',
            RAWLEAD_CHILD_URI . '/assets/js/rawlead-cabinet.js',
            [],
            RAWLEAD_CHILD_VERSION,
            true
        );
        wp_localize_script('rawlead-cabinet', 'rawleadCabinet', [
            'restReplies'          => esc_url_raw(rest_url('rawlead/v1/me/replies')),
            'restTags'             => esc_url_raw(rest_url('rawlead/v1/me/tags')),
            'restSkills'           => esc_url_raw(rest_url('rawlead/v1/skills/catalog')),
            'restAuth'             => esc_url_raw(rest_url('rawlead/v1/auth/telegram')),
            'restBotSession'       => esc_url_raw(rest_url('rawlead/v1/auth/bot-session')),
            'restBotComplete'      => esc_url_raw(rest_url('rawlead/v1/auth/bot-complete')),
            'restQrImage'          => esc_url_raw(rest_url('rawlead/v1/auth/qr-image')),
            'botLoginUrl'          => esc_url_raw('https://t.me/' . rawlead_tg_login_bot_username() . '?start=login'),
            'restSubscription'          => esc_url_raw(rest_url('rawlead/v1/me/subscription')),
            'restTrialStart'            => esc_url_raw(rest_url('rawlead/v1/me/subscription/trial-start')),
            'restNotificationSettings'  => esc_url_raw(rest_url('rawlead/v1/me/notification-settings')),
            'lentaUrl'                  => esc_url_raw(rawlead_page_url('lenta')),
            'pricingUrl'           => esc_url_raw(rawlead_page_url('pricing')),
            'botPayUrl'            => esc_url_raw('https://t.me/' . rawlead_tg_login_bot_username() . '?start=pay'),
            'tgBotUsername'        => rawlead_tg_login_bot_username(),
            'tgBotId'              => rawlead_tg_login_bot_id(),
            'tgLoginFallbackUrl'   => rawlead_tg_login_fallback_url(),
            'tgLoginDev'           => defined('RAWLEAD_TG_LOGIN_DEV') && RAWLEAD_TG_LOGIN_DEV,
            'tgLoginWidgetAllowed' => rawlead_tg_login_widget_allowed(),
            'localPort'            => defined('RAWLEAD_LOCAL_SITE_PORT') ? (string) RAWLEAD_LOCAL_SITE_PORT : '10007',
            'loginUrl'             => rawlead_cabinet_login_url(),
            'nonce'                => wp_create_nonce('wp_rest'),
            'apiBase'              => rawlead_api_base_url(),
        ]);
    }

    if (rawlead_is_shell_page()) {
        wp_enqueue_script(
            'rawlead-support',
            RAWLEAD_CHILD_URI . '/assets/js/rawlead-support.js',
            [],
            RAWLEAD_CHILD_VERSION,
            true
        );
        wp_localize_script('rawlead-support', 'rawleadSupport', [
            'restTicket' => esc_url_raw(rest_url('rawlead/v1/support/ticket')),
            'restThread' => esc_url_raw(rest_url('rawlead/v1/support/thread')),
            'restUnread' => esc_url_raw(rest_url('rawlead/v1/support/unread')),
        ]);
    }

    if (is_page(['lenta', 'cabinet']) || is_front_page()) {
        $pv_slug = is_front_page() ? '' : (string) get_post_field('post_name', get_queried_object_id());
        $pv_path = $pv_slug === '' ? '/' : '/' . $pv_slug;
        wp_register_script('rawlead-pageview', false, [], RAWLEAD_CHILD_VERSION, true);
        wp_enqueue_script('rawlead-pageview');
        wp_add_inline_script(
            'rawlead-pageview',
            sprintf(
                '(function(){var u=%1$s,p=%2$s,k="rawlead_vid_v1",v="";try{v=localStorage.getItem(k)||"";if(!v){v=(Date.now().toString(36)+Math.random().toString(36).slice(2,10));localStorage.setItem(k,v);}}catch(e){}fetch(u,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({path:p,visitor_id:v}),keepalive:true}).catch(function(){});})();',
                wp_json_encode(esc_url_raw(rest_url('rawlead/v1/admin/pageview'))),
                wp_json_encode($pv_path)
            )
        );
    }
}, 20);

add_filter('body_class', static function (array $classes): array {
    $classes[] = 'rawlead-site';
    if (is_front_page()) {
        $classes[] = 'rawlead-front';
    } elseif (rawlead_is_app_page()) {
        $classes[] = 'rawlead-inner';
        $classes[] = 'rawlead-app-page';
    } elseif (rawlead_is_inner_shell_page()) {
        $classes[] = 'rawlead-inner';
    }
    if (is_page()) {
        $post = get_queried_object();
        if ($post instanceof WP_Post && $post->post_name !== '') {
            $classes[] = 'page-' . sanitize_html_class($post->post_name);
        }
    }
    return $classes;
});

/** Marketing pages: custom header/footer; hide Kadence chrome. */
add_action('wp_head', static function (): void {
    if (!rawlead_is_shell_page()) {
        return;
    }
    echo "<style>#masthead,#colophon,.site-footer,.entry-hero{display:none!important}</style>\n";
}, 99);

add_action('init', static function (): void {
    register_block_pattern_category('rawlead', [
        'label' => __('RawLead', 'rawlead-kadence-child'),
    ]);

    $pattern_files = glob(RAWLEAD_CHILD_DIR . '/patterns/*.php') ?: [];
    foreach ($pattern_files as $file) {
        $slug = 'rawlead-kadence-child/' . basename($file, '.php');
        $content = file_get_contents($file);
        if ($content === false) {
            continue;
        }
        if (preg_match('/\* Title:\s*(.+)/', $content, $m)) {
            $title = trim($m[1]);
        } else {
            $title = basename($file, '.php');
        }
        $markup = preg_replace('/^<\?php.*?\?>\s*/s', '', $content);
        if (!is_string($markup) || trim($markup) === '') {
            continue;
        }
        register_block_pattern($slug, [
            'title'       => $title,
            'categories'  => ['rawlead'],
            'content'     => trim($markup),
            'description' => __('RawLead editorial block', 'rawlead-kadence-child'),
        ]);
    }
});

/**
 * Append CTA on inner pages (plugin HTML has no buttons).
 */
add_filter('the_content', static function (string $content): string {
    if (!is_page() || is_front_page() || !in_the_loop() || !is_main_query()) {
        return $content;
    }
    $post = get_queried_object();
    if (!$post instanceof WP_Post) {
        return $content;
    }
    $slug = $post->post_name;

    if (rawlead_is_inner_shell_page()) {
        $content = rawlead_format_inner_content($content, $slug);
    }
    $pricing = rawlead_page_url('pricing');
    $contact = rawlead_page_url('contact');
    $how = rawlead_page_url('how');

    $cta = match ($slug) {
        'how' => sprintf(
            '<p class="rl-page-cta"><a class="rl-btn rl-btn--primary" href="%s">%s</a></p>',
            esc_url(rawlead_page_url('lenta')),
            esc_html__('Смотреть ленту →', 'rawlead-kadence-child')
        ),
        'pricing' => sprintf(
            '<p class="rl-page-cta"><a class="rl-btn rl-btn--primary" href="%s">%s</a> '
            . '<a class="rl-btn rl-btn--ghost" href="%s">%s</a></p>',
            esc_url(rawlead_page_url('lenta')),
            esc_html__('Смотреть ленту', 'rawlead-kadence-child'),
            esc_url(rawlead_page_url('cabinet')),
            esc_html__('Вход в ЛК', 'rawlead-kadence-child')
        ),
        'faq' => sprintf(
            '<p class="rl-page-cta"><a class="rl-btn rl-btn--primary" href="%s">Контакты</a></p>',
            esc_url($contact)
        ),
        'contact' => sprintf(
            '<p class="rl-page-cta"><a class="rl-btn rl-btn--primary" href="https://t.me/rcnn43" target="_blank" rel="noopener">Telegram @rcnn43</a> '
            . '<a class="rl-link-arrow" href="%s">Как это работает →</a></p>',
            esc_url($how)
        ),
        default => '',
    };

    return $content . $cta;
}, 12);

/**
 * Local + Telegram Login: BotFather domain 127.0.0.1 — редирект /cabinet/ с .local на порт Local.
 */
add_filter('redirect_canonical', static function ($redirect_url, $requested_url) {
    if (is_page('cabinet') && str_starts_with(strtolower((string) ($_SERVER['HTTP_HOST'] ?? '')), '127.0.0.1')) {
        return false;
    }
    return $redirect_url;
}, 10, 2);

add_action('template_redirect', static function (): void {
    if (!is_page('cabinet')) {
        return;
    }
    $host = strtolower((string) ($_SERVER['HTTP_HOST'] ?? ''));
    if ($host === '' || str_starts_with($host, '127.0.0.1')) {
        return;
    }
    if (!str_contains($host, 'radarzakaz.local')) {
        return;
    }
    $port = defined('RAWLEAD_LOCAL_SITE_PORT') ? (string) RAWLEAD_LOCAL_SITE_PORT : '10007';
    $target = 'http://127.0.0.1:' . $port . '/cabinet/';
    $qs = isset($_SERVER['QUERY_STRING']) && $_SERVER['QUERY_STRING'] !== ''
        ? '?' . (string) $_SERVER['QUERY_STRING']
        : '';
    wp_safe_redirect($target . $qs, 302);
    exit;
}, 1);
