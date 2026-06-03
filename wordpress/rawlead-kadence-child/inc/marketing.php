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
        'how'     => __('Пять шагов: от биржи до твоего отклика', 'rawlead-kadence-child'),
        'pricing' => __('Один тариф. Всё включено.', 'rawlead-kadence-child'),
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
<p><strong>300 ⭐ Stars в месяц</strong> — примерно <strong>400–720 ₽</strong> при покупке в Telegram.</p>
<p>Для любой ниши — дизайн, тексты, код, маркетинг. ИИ знает твои теги.</p>
<ul>
<li>Лента только с заказами под твой стек</li>
<li>Черновик отклика — ИИ пишет, ты правишь. Для каждого — своя формулировка.</li>
<li>Пуш в Telegram — только при хорошем совпадении</li>
</ul>
<h2>Оплата</h2>
<p>Оплата через Telegram Stars — @rawlead_bot /pay или кнопка «Оплатить Stars» в кабинете.</p>
<p><a href="' . $cabinet . '">Вход в кабинет →</a> · <a href="' . $lenta . '">Смотреть ленту →</a></p>
<p><a class="rl-btn rl-btn--primary" href="' . $bot_pay . '">Подключить — 300 ⭐ в Telegram →</a></p>',
        'how'     => '<h2>1. Указываешь навыки</h2>
<p>Выбери нишу и добавь теги — дизайн, разработка, маркетинг, тексты. Чем точнее профиль, тем лучше совместимость.</p>
<h2>2. Настраиваешь профиль</h2>
<p>Профиль хранит твои навыки. Лента автоматически подбирает заказы — менять настройки каждый раз не нужно.</p>
<h2>3. Радар следит 24/7</h2>
<p>Десятки источников проверяются автоматически. Дубликаты, спам и нерелевантные объявления не попадают в ленту.</p>
<h2>4. ИИ читает суть заказа</h2>
<p>Система понимает задачу, решает, что нужно для её выполнения, и сверяет с твоим стеком.</p>
<h2>5. Ты откликаешься сам</h2>
<p>Черновик уже готов — для тебя написан отдельно, не скопирован с чужого отклика. Поправь детали и отправь. Мы не пишем заказчикам за тебя.</p>
<p><strong>Один поток вместо десятка вкладок.</strong> Premium с лентой без задержки и push — от <strong>790 ₽/мес</strong> или 300 ⭐.</p>
<p><a class="rl-btn rl-btn--primary" href="' . $lenta . '">Смотреть ленту →</a> · <a href="' . esc_url(rawlead_page_url('pricing')) . '">Тариф 790 ₽ →</a> · <a href="' . $cabinet . '">Войти в кабинет →</a></p>',
        'faq'     => '<details class="rl-faq-item"><summary><h2>Это автоматическая рассылка заказчикам?</h2></summary>
<p>Нет. RawLead только находит заказы и присылает тебе уведомление. Писать заказчикам — сам, в удобное время. Никакого автоспама.</p></details>
<details class="rl-faq-item"><summary><h2>Подходит ли для нетехнических специалистов?</h2></summary>
<p>Да. RawLead работает с четырьмя нишами: разработка, дизайн, маркетинг, тексты. Добавь свои навыки — ИИ найдёт подходящие заказы под твой профиль.</p></details>
<details class="rl-faq-item"><summary><h2>Какие источники поддерживаются?</h2></summary>
<p>FL.ru, Kwork, YouDo, Freelance.ru, FreelanceJob, Пчёл.нет, Telegram-каналы. База расширяется.</p></details>
<details class="rl-faq-item"><summary><h2>Нужен ли мой основной аккаунт Telegram?</h2></summary>
<p>Да — для входа через кнопку на сайте или команду /login в @rawlead_bot. Аккаунт нужен только для авторизации, ничего без твоего ведома не отправляется.</p></details>
<details class="rl-faq-item"><summary><h2>Не получу ли бан на бирже?</h2></summary>
<p>Нет. Отклики пишешь ты — своими словами, в своё время. RawLead только подбирает заказы и черновик. Автоспама с твоего аккаунта нет.</p></details>
<details class="rl-faq-item"><summary><h2>Как начать пользоваться?</h2></summary>
<p>Открой <a href="' . $lenta . '">ленту заказов</a> — регистрация не нужна. Чтобы настроить навыки и получать черновики откликов, войди через Telegram в <a href="' . $cabinet . '">кабинете</a>.</p></details>
<details class="rl-faq-item"><summary><h2>Сервис платный?</h2></summary>
<p>Лента открыта бесплатно — с задержкой 15 мин. Premium (<strong>790 ₽/мес</strong> или 300 ⭐) — без задержки, уникальные черновики, push. <a href="' . esc_url(rawlead_page_url('pricing')) . '">Тарифы →</a></p></details>
<details class="rl-faq-item"><summary><h2>Почему лимит 10 откликов на заказ?</h2></summary>
<p>Чтобы на один hot-заказ не съехалась толпа одинаковых ботов. Каждый отклик — свой. Когда слоты кончились, заказ исчезает из ленты — бери другой матч.</p></details>
<details class="rl-faq-item"><summary><h2>Есть пробный период?</h2></summary>
<p>Да — 3 дня полного Premium один раз после входа. Без карты. Потом — <strong>790 ₽/мес</strong> или Stars. <a href="' . $cabinet . '">Кабинет →</a></p></details>',
        default   => null,
    };
}
