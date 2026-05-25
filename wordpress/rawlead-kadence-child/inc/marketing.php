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

function rawlead_inner_page_lead(string $slug): string {
    return match ($slug) {
        'how'     => __('Пять шагов: от навыков до вашего отклика', 'rawlead-kadence-child'),
        'pricing' => __('Тарифы для соло и команды — оплата скоро', 'rawlead-kadence-child'),
        'faq'     => __('Коротко о RawLead для любой ниши фриланса', 'rawlead-kadence-child'),
        'contact' => __('Ранний доступ — Telegram или форма', 'rawlead-kadence-child'),
        'lenta'   => __('Открытый рынок заказов с бирж и Telegram', 'rawlead-kadence-child'),
        'cabinet' => __('Персональная лента по вашим тегам — скоро', 'rawlead-kadence-child'),
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
        $formatted = preg_replace(
            '/(<h2[^>]*>.*?<\/h2>)\s*(<p>.*?<\/p>)/is',
            '<section class="rl-faq-card">$1$2</section>',
            $content
        );

        return is_string($formatted) ? $formatted : $content;
    }

    return $content;
}
