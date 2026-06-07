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
        'contact' => __('Напишите нам — ответим в окне поддержки', 'rawlead-kadence-child'),
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

    if ($slug === 'contact') {
        return $content . rawlead_contact_form_html();
    }

    return $content;
}

/** O116-W4 — форма на /contact/ (тот же API, что FAB). */
function rawlead_contact_form_html(): string {
    return '<form class="rl-contact-form" id="rl-contact-form" novalidate>'
        . '<label class="rl-support-modal__label" for="rl-contact-name">'
        . esc_html__('Имя (необязательно)', 'rawlead-kadence-child')
        . '</label>'
        . '<input class="rl-contact-form__input" type="text" id="rl-contact-name" name="name" autocomplete="name" />'
        . '<label class="rl-support-modal__label" for="rl-contact-message">'
        . esc_html__('Сообщение', 'rawlead-kadence-child')
        . '</label>'
        . '<textarea class="rl-support-modal__input rl-contact-form__textarea" id="rl-contact-message" name="message" rows="5" required '
        . 'placeholder="' . esc_attr__('Опиши вопрос или проблему', 'rawlead-kadence-child') . '"></textarea>'
        . '<button type="submit" class="rl-btn rl-support-modal__submit" id="rl-contact-submit">'
        . esc_html__('Отправить →', 'rawlead-kadence-child')
        . '</button>'
        . '<p class="rl-contact-form__success" id="rl-contact-success" hidden>'
        . esc_html__('Спасибо. Ответ появится в «Поддержка» на сайте.', 'rawlead-kadence-child')
        . '</p>'
        . '</form>';
}

/** O116 Z4 — FAQ три группы + Q10. */
function rawlead_faq_groups_html(string $lenta, string $cabinet): string {
    $pricing = esc_url(rawlead_page_url('pricing'));

    return '<div class="rl-faq-groups">' .
        '<div class="rl-faq-group is-open" data-index="0">' .
        '<button type="button" class="rl-faq-group__header">' . esc_html__('Начало', 'rawlead-kadence-child') . '</button>' .
        '<div class="rl-faq-group__body">' .
        '<details class="rl-faq-item"><summary><h2>' . esc_html__('Как начать пользоваться?', 'rawlead-kadence-child') . '</h2></summary>' .
        '<p>Открой <a href="' . $lenta . '">ленту заказов</a> — регистрация не нужна. Чтобы настроить навыки и получать черновики откликов, войди через Telegram в <a href="' . $cabinet . '">кабинете</a>.</p></details>' .
        '<details class="rl-faq-item"><summary><h2>' . esc_html__('Это автоматическая рассылка заказчикам?', 'rawlead-kadence-child') . '</h2></summary>' .
        '<p>Нет. RawLead только находит заказы и присылает тебе уведомление. Писать заказчикам — сам, в удобное время. Никакого автоспама.</p></details>' .
        '<details class="rl-faq-item"><summary><h2>' . esc_html__('Нужен ли мой основной аккаунт Telegram?', 'rawlead-kadence-child') . '</h2></summary>' .
        '<p>Да, авторизация на сайте происходит через официальный безопасный виджет Telegram. Сервер получает только твой публичный ID и юзернейм. RawLead физически не имеет доступа к твоим личным перепискам, контактам или паролям — всё полностью безопасно.</p></details>' .
        '</div></div>' .
        '<div class="rl-faq-group" data-index="1">' .
        '<button type="button" class="rl-faq-group__header">' . esc_html__('Как работает', 'rawlead-kadence-child') . '</button>' .
        '<div class="rl-faq-group__body">' .
        '<details class="rl-faq-item"><summary><h2>' . esc_html__('Подходит ли для нетехнических специалистов?', 'rawlead-kadence-child') . '</h2></summary>' .
        '<p>Да. RawLead работает с четырьмя нишами: разработка, дизайн, маркетинг, тексты. Добавь свои навыки — ИИ найдёт подходящие заказы под твой профиль.</p></details>' .
        '<details class="rl-faq-item"><summary><h2>' . esc_html__('Какие источники поддерживаются?', 'rawlead-kadence-child') . '</h2></summary>' .
        '<p>FL.ru, Kwork, YouDo, Freelance.ru, FreelanceJob, Пчёл.нет, Telegram-каналы. База расширяется.</p></details>' .
        '<details class="rl-faq-item"><summary><h2>' . esc_html__('Не получу ли бан на бирже?', 'rawlead-kadence-child') . '</h2></summary>' .
        '<p>Нет. Отклики пишешь ты — своими словами, в своё время. RawLead только подбирает заказы и черновик. Автоспама с твоего аккаунта нет.</p></details>' .
        '<details class="rl-faq-item"><summary><h2>' . esc_html__('Почему лимит 10 откликов в час?', 'rawlead-kadence-child') . '</h2></summary>' .
        '<p>Чтобы защитить твой аккаунт от спам-фильтров бирж, система ограничивает интенсивность: не более <strong>10 откликов в час</strong>. Это сохраняет качество и не даёт твоим предложениям теряться в спаме.</p></details>' .
        '</div></div>' .
        '<div class="rl-faq-group" data-index="2">' .
        '<button type="button" class="rl-faq-group__header">' . esc_html__('Premium', 'rawlead-kadence-child') . '</button>' .
        '<div class="rl-faq-group__body">' .
        '<details class="rl-faq-item"><summary><h2>' . esc_html__('Сервис платный?', 'rawlead-kadence-child') . '</h2></summary>' .
        '<p>Лента открыта бесплатно — с задержкой 15 мин. Для авторизованных и Premium пользователей (<strong>790 ₽/мес</strong> или 600 ⭐) — без задержки, уникальные черновики, push. <a href="' . $pricing . '">Тарифы →</a></p></details>' .
        '<details class="rl-faq-item"><summary><h2>' . esc_html__('Есть пробный период?', 'rawlead-kadence-child') . '</h2></summary>' .
        '<p>Да — 3 дня полного Premium один раз после входа через Telegram. Без карты и скрытых условий. Потом — <strong>790 ₽/мес</strong> или 600 ⭐ в @rawlead_bot /pay. <a href="' . $pricing . '">Тарифы →</a></p></details>' .
        '<details class="rl-faq-item"><summary><h2>' . esc_html__('Зачем Premium, если лента и так без задержки после входа?', 'rawlead-kadence-child') . '</h2></summary>' .
        '<p>После входа через Telegram — лента сразу. Это бесплатно. Premium даёт: уникальный черновик отклика под твой профиль · push в Telegram при матче · inbox с черновиками · умный лимит <strong>10 откликов в час</strong>.</p></details>' .
        '<details class="rl-faq-item"><summary><h2>' . esc_html__('Почему лимит 10 черновиков на один заказ?', 'rawlead-kadence-child') . '</h2></summary>' .
        '<p>Чтобы на один hot-заказ не съехалась толпа одинаковых ботов — каждый отклик свой. Когда места заняты, кнопка «Написать отклик» становится серой, но заказ остаётся в ленте — можно посмотреть детали и взять другой матч.</p></details>' .
        '</div></div>' .
        '</div>';
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
<p><strong>600 ⭐ Stars в месяц</strong> — оплата в Telegram.</p>
<p>Для любой ниши — дизайн, тексты, код, маркетинг. ИИ знает твои теги.</p>
<ul>
<li>Лента только с заказами под твой стек</li>
<li>Черновик отклика — ИИ пишет, ты правишь. Для каждого — своя формулировка.</li>
<li>Пуш в Telegram — только при хорошем совпадении</li>
</ul>
<h2>Оплата</h2>
<p>Оплата через Telegram Stars — @rawlead_bot /pay или кнопка «Оплатить Stars» в кабинете.</p>
<p><a href="' . $cabinet . '">Вход в кабинет →</a> · <a href="' . $lenta . '">Продолжить с ограничениями (Free) →</a></p>
<p><a class="rl-btn rl-btn--primary" href="' . $bot_pay . '">Подключить — 600 ⭐ в Telegram →</a></p>',
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
<h2>Защита от спама</h2>
<p>Система жёстко контролирует нагрузку: умный лимит — <strong>10 откликов в час</strong>. Мы защищаем твой аккаунт от спам-фильтров бирж и гарантируем заказчикам качество.</p>
<p><strong>Один поток вместо десятка вкладок.</strong> Premium с лентой без задержки и push — от <strong>790 ₽/мес</strong> или 600 ⭐.</p>
<p><a class="rl-btn rl-btn--primary" href="' . $cabinet . '">Войти в кабинет →</a></p>',
        'faq'     => rawlead_faq_groups_html($lenta, $cabinet),
        default   => null,
    };
}
