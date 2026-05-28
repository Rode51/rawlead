<?php
/**
 * Marketing / shell pages helpers.
 *
 * @package RawLead_Kadence_Child
 */

declare(strict_types=1);

if (!defined('ABSPATH')) {
    exit;
}

/** @return list<string> */
function rawlead_shell_slugs(): array {
    return ['home', 'how', 'pricing', 'faq', 'contact', 'lenta', 'cabinet'];
}

/** Продуктовые страницы ленты / кабинета (без inner-hero из page.php). */
function rawlead_is_app_page(): bool {
    if (!is_page()) {
        return false;
    }
    $post = get_queried_object();
    return $post instanceof WP_Post
        && in_array($post->post_name, ['lenta', 'cabinet'], true);
}

function rawlead_is_shell_page(): bool {
    if (is_front_page()) {
        return true;
    }
    if (!is_page()) {
        return false;
    }
    $post = get_queried_object();
    return $post instanceof WP_Post
        && in_array($post->post_name, rawlead_shell_slugs(), true);
}

function rawlead_is_inner_shell_page(): bool {
    return rawlead_is_shell_page() && !is_front_page();
}

/** Local WP / 127.0.0.1 — не prod rawlead.ru. */
function rawlead_is_local_dev(): bool {
    if (defined('RAWLEAD_TG_LOGIN_DEV') && RAWLEAD_TG_LOGIN_DEV) {
        return true;
    }
    if (function_exists('wp_get_environment_type') && wp_get_environment_type() === 'local') {
        return true;
    }
    $host = strtolower((string) ($_SERVER['HTTP_HOST'] ?? ''));
    if ($host === 'localhost' || str_starts_with($host, '127.0.0.1')) {
        return true;
    }
    return str_contains($host, 'radarzakaz.local');
}

/** @return list<string> */
function rawlead_tg_login_hosts(): array {
    return ['rawlead.ru', 'www.rawlead.ru'];
}

/** Можно монтировать Telegram Login Widget на текущем host. */
function rawlead_tg_login_widget_allowed(): bool {
    if (defined('RAWLEAD_TG_LOGIN_DEV') && RAWLEAD_TG_LOGIN_DEV) {
        $host = strtolower((string) ($_SERVER['HTTP_HOST'] ?? ''));
        return str_starts_with($host, '127.0.0.1');
    }
    if (rawlead_is_local_dev()) {
        $host = strtolower((string) ($_SERVER['HTTP_HOST'] ?? ''));
        return str_starts_with($host, '127.0.0.1');
    }
    $host = strtolower(preg_replace('/:\d+$/', '', (string) ($_SERVER['HTTP_HOST'] ?? '')));
    return in_array($host, rawlead_tg_login_hosts(), true);
}

/** URL страницы входа: prod → /cabinet/, local → 127.0.0.1:port. */
function rawlead_cabinet_login_url(): string {
    if (rawlead_is_local_dev()) {
        $port = defined('RAWLEAD_LOCAL_SITE_PORT') ? (string) RAWLEAD_LOCAL_SITE_PORT : '10007';
        return 'http://127.0.0.1:' . $port . '/cabinet/';
    }
    return home_url('/cabinet/');
}

function rawlead_inner_page_lead(string $slug): string {
    return match ($slug) {
        'how'     => __('Пять шагов: от навыков до вашего отклика', 'rawlead-kadence-child'),
        'pricing' => __('Тариф ИИ-агент — 300 Telegram Stars/мес (~400–720 ₽)', 'rawlead-kadence-child'),
        'faq'     => __('Коротко о RawLead для любой ниши фриланса', 'rawlead-kadence-child'),
        'contact' => __('Свяжитесь с нами — Telegram или форма', 'rawlead-kadence-child'),
        'lenta'   => __('Открытый рынок заказов с бирж и Telegram', 'rawlead-kadence-child'),
        'cabinet' => __('Персональная лента по вашим тегам и статус подписки', 'rawlead-kadence-child'),
        default   => '',
    };
}

/**
 * Wrap plugin HTML into landing-style cards.
 */
function rawlead_format_inner_content(string $content, string $slug): string {
    if ($content === '') {
        return $content;
    }

    if ($slug === 'how' || $slug === 'pricing') {
        $formatted = preg_replace(
            '/(<h2[^>]*>.*?<\/h2>)(.*?)(?=<h2|$)/is',
            '<section class="rl-block-card">$1<div class="rl-block-card__body">$2</div></section>',
            $content
        );

        return is_string($formatted) ? $formatted : $content;
    }

    if ($slug === 'faq') {
        return $content;
    }

    return $content;
}
