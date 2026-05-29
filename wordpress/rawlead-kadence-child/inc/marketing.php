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
        'how'     => __('Три шага: от радара до твоего отклика', 'rawlead-kadence-child'),
        'pricing' => __('Тариф ИИ-агент — 300 Telegram Stars/мес (~400–720 ₽)', 'rawlead-kadence-child'),
        'faq'     => __('Коротко о RawLead для любой ниши фриланса', 'rawlead-kadence-child'),
        'contact' => __('Telegram или email — без формы', 'rawlead-kadence-child'),
        'lenta'   => __('Открытый рынок заказов с бирж и Telegram', 'rawlead-kadence-child'),
        'cabinet' => __('Inbox откликов, навыки и статус подписки', 'rawlead-kadence-child'),
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
        return $content;
    }

    if ($slug === 'faq') {
        return $content;
    }

    return $content;
}

/**
 * Canonical HTML for inner shell pages (overrides WP editor copy on deploy).
 */
function rawlead_inner_page_html(string $slug): ?string {
    $lenta = esc_url(rawlead_page_url('lenta'));
    $cabinet = esc_url(rawlead_page_url('cabinet'));
    $bot_pay = esc_url('https://t.me/' . rawlead_tg_login_bot_username() . '?start=pay');

    return match ($slug) {
        'pricing' => '<h2>ИИ-агент</h2>
<p><strong>300 ⭐ Stars / мес</strong> — при покупке Stars в Telegram это примерно <strong>400–720 ₽</strong> (зависит от пакета).</p>
<p>Для любой ниши — дизайн, тексты, код, маркетинг. ИИ знает твои теги.</p>
<ul>
<li>Персональная лента по твоим навыкам</li>
<li>Черновик отклика за одну кнопку</li>
<li>Push в Telegram при новом матче</li>
</ul>
<h2>Оплата</h2>
<p><strong>Telegram Stars</strong> — 300 ⭐ в @rawlead_bot или кнопка «Оплатить Stars» в кабинете.</p>
<p><a href="' . $cabinet . '">Вход в кабинет →</a> · <a href="' . $lenta . '">Смотреть ленту →</a></p>
<p><a class="rl-btn rl-btn--primary" href="' . $bot_pay . '">Подключить — 300 ⭐ в Telegram →</a></p>',
        'how'     => '<h2>1. Указываешь навыки</h2>
<p>Выбери свою нишу и добавь теги — дизайн, копирайт, разработка, маркетинг, SMM, переводы или любая другая специализация. Можно настроить так точно, как нужно тебе.</p>
<h2>2. Настраиваешь фильтры</h2>
<p>Минимальная совместимость, источник, категория. Система запоминает твой профиль — менять каждый раз не нужно.</p>
<h2>3. Радар следит 24/7</h2>
<p>Десятки источников проверяются автоматически. Дубликаты, спам и нерелевантные объявления не попадают в ленту.</p>
<h2>4. Нейросеть мэтчит технологии</h2>
<p>Система не просто ищет ключевые слова. ИИ понимает суть заказа, решает, какие инструменты и библиотеки нужны для выполнения, и сверяет это с твоим стеком.</p>
<h2>5. Ты откликаешься сам</h2>
<p>Готовый черновик отклика — поправить и отправить вручную. Мы не пишем заказчикам за тебя и не отправляем ничего автоматически.</p>
<p><strong>Один поток вместо десятка вкладок.</strong> Ты тратишь время на работу, а не на мониторинг.</p>
<p><a class="rl-btn rl-btn--primary" href="' . $lenta . '">Смотреть ленту →</a> · <a href="' . $cabinet . '">Войти в кабинет →</a></p>',
        default   => null,
    };
}
