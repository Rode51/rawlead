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
    return ['home', 'how', 'pricing', 'faq', 'contact', 'lenta', 'cabinet', 'quiz'];
}

/** Продуктовые страницы ленты / кабинета (без inner-hero из page.php). */
function rawlead_is_app_page(): bool {
    if (!is_page()) {
        return false;
    }
    $post = get_queried_object();
    return $post instanceof WP_Post
        && in_array($post->post_name, ['lenta', 'cabinet', 'quiz'], true);
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
        'pricing' => __('Пробуй 3 дня бесплатно — автоматически при первом входе.', 'rawlead-kadence-child'),
        'faq'     => __('Коротко о RawLead для любой ниши фриланса', 'rawlead-kadence-child'),
        'contact' => '',
        'lenta'   => __('Открытый рынок заказов с бирж и Telegram', 'rawlead-kadence-child'),
        'cabinet' => __('Inbox откликов, навыки и статус подписки', 'rawlead-kadence-child'),
        'quiz'    => __('Тест-настройка ленты под твой стек', 'rawlead-kadence-child'),
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
        return $content;
    }

    return $content;
}

/** O215 — /contact/ одна NEO-карточка, без формы и beta. */
function rawlead_contact_page_html(): string {
    return '<div class="rl-contact-card">'
        . '<p class="rl-contact-card__lead">'
        . esc_html__('Написать напрямую · @rcnn43 в Telegram', 'rawlead-kadence-child')
        . '</p>'
        . '<a class="rl-btn rl-btn--primary" href="https://t.me/rcnn43" target="_blank" rel="noopener noreferrer">'
        . esc_html__('Открыть Telegram →', 'rawlead-kadence-child')
        . '</a>'
        . '</div>';
}

/** @deprecated O215 — форма убрана с /contact/ */
function rawlead_contact_form_html(): string {
    return '';
}

/** O116 Z4 — FAQ три группы + Q10. */
function rawlead_faq_groups_html(string $lenta, string $cabinet): string {
    $pricing = esc_url(rawlead_page_url('pricing'));

    return '<div class="rl-faq-groups">' .
        '<div class="rl-faq-group is-open" data-index="0">' .
        '<button type="button" class="rl-faq-group__header">' . esc_html__('Начало', 'rawlead-kadence-child') . '</button>' .
        '<div class="rl-faq-group__body">' .
        '<details class="rl-faq-item"><summary><h2>' . esc_html__('Как начать пользоваться?', 'rawlead-kadence-child') . '</h2></summary>' .
        '<p>Открой <a href="' . $lenta . '">ленту заказов</a> — регистрация не нужна. Пройди квиз — ИИ узнает твой профиль. Войди через Telegram в <a href="' . $cabinet . '">кабинете</a> — черновики и персональная лента.</p></details>' .
        '<details class="rl-faq-item"><summary><h2>' . esc_html__('Это автоматическая рассылка заказчикам?', 'rawlead-kadence-child') . '</h2></summary>' .
        '<p>Нет. RawLead только находит заказы и присылает тебе уведомление. Писать заказчикам — сам, в удобное время. Никакого автоспама.</p></details>' .
        '<details class="rl-faq-item"><summary><h2>' . esc_html__('Нужен ли мой основной аккаунт Telegram?', 'rawlead-kadence-child') . '</h2></summary>' .
        '<p>Да, авторизация на сайте происходит через официальный безопасный виджет Telegram. Сервер получает только твой публичный ID и юзернейм. RawLead физически не имеет доступа к твоим личным перепискам, контактам или паролям — всё полностью безопасно.</p></details>' .
        '</div></div>' .
        '<div class="rl-faq-group" data-index="1">' .
        '<button type="button" class="rl-faq-group__header">' . esc_html__('Как работает', 'rawlead-kadence-child') . '</button>' .
        '<div class="rl-faq-group__body">' .
        '<details class="rl-faq-item"><summary><h2>' . esc_html__('Подходит ли для нетехнических специалистов?', 'rawlead-kadence-child') . '</h2></summary>' .
        '<p>Да. RawLead работает с четырьмя нишами: разработка, дизайн, маркетинг, тексты. Пройди квиз — ИИ узнает твой профиль и найдёт совпадения.</p></details>' .
        '<details class="rl-faq-item"><summary><h2>' . esc_html__('Как система подбирает заказы именно под меня?', 'rawlead-kadence-child') . '</h2></summary>' .
        '<p>Сначала — по профилю из квиза. Потом ИИ запоминает, на что ты откликаешься, и уточняет % совпадения. Лента становится точнее сама.</p></details>' .
        '<details class="rl-faq-item"><summary><h2>' . esc_html__('Какие источники поддерживаются?', 'rawlead-kadence-child') . '</h2></summary>' .
        '<p>FL.ru, Kwork, YouDo, Freelance.ru, FreelanceJob, Пчёл.нет, Telegram-каналы. База расширяется.</p></details>' .
        '<details class="rl-faq-item"><summary><h2>' . esc_html__('Не получу ли бан на бирже?', 'rawlead-kadence-child') . '</h2></summary>' .
        '<p>Нет. Отклики пишешь ты — своими словами, в своё время. RawLead только подбирает заказы и черновик. Автоспама с твоего аккаунта нет.</p></details>' .
        '<details class="rl-faq-item"><summary><h2>' . esc_html__('Почему лимит 5 откликов в час?', 'rawlead-kadence-child') . '</h2></summary>' .
        '<p>Чтобы защитить твой аккаунт от спам-фильтров бирж, система ограничивает интенсивность: не более <strong>5 откликов в час (включая Premium)</strong>. Это сохраняет качество и не даёт твоим предложениям теряться в спаме.</p></details>' .
        '<details class="rl-faq-item"><summary><h2>' . esc_html__('Что такое % совпадения?', 'rawlead-kadence-child') . '</h2></summary>' .
        '<p>Это насколько заказ подходит под твой профиль из квиза. 90%+ — отлично совпадает. Алгоритм учитывает категорию, навыки и тип задачи. Не рейтинг среди других фрилансеров — только твой личный match.</p></details>' .
        '</div></div>' .
        '<div class="rl-faq-group" data-index="2">' .
        '<button type="button" class="rl-faq-group__header">' . esc_html__('Premium', 'rawlead-kadence-child') . '</button>' .
        '<div class="rl-faq-group__body">' .
        '<details class="rl-faq-item"><summary><h2>' . esc_html__('Сервис платный?', 'rawlead-kadence-child') . '</h2></summary>' .
        '<p>Лента открыта бесплатно — с задержкой <strong>30 мин</strong>. Для Trial и Premium (<strong>790 ₽/мес</strong>) — без задержки, персональная лента, черновики, push. <a href="' . $pricing . '">Тарифы →</a></p></details>' .
        '<details class="rl-faq-item"><summary><h2>' . esc_html__('Есть пробный период?', 'rawlead-kadence-child') . '</h2></summary>' .
        '<p>Да — <strong>бесплатно, автоматически при входе</strong> · 3 дня Premium (1× на аккаунт TG). Далее — <strong>790 ₽/мес</strong>. <a href="' . $pricing . '">Тарифы →</a></p></details>' .
        '<details class="rl-faq-item"><summary><h2>' . esc_html__('Есть ли автопродление?', 'rawlead-kadence-child') . '</h2></summary>' .
        '<p>Нет. После Trial — лента без персонализации. Продлить Premium — вручную.</p></details>' .
        '<details class="rl-faq-item"><summary><h2>' . esc_html__('Зачем Premium, если лента и так без задержки после входа?', 'rawlead-kadence-child') . '</h2></summary>' .
        '<p>После первого входа — 3 дня Trial бесплатно: персональная лента, черновики, push. После Trial — лента с задержкой 30 мин и без персонализации. Premium возвращает всё это за 790 ₽/мес.</p></details>' .
        '</div></div>' .
        '</div>';
}

/**
 * Canonical HTML for inner shell pages (overrides WP editor copy on deploy).
 */
function rawlead_inner_page_html(string $slug): ?string {
    $lenta = esc_url(rawlead_page_url('lenta'));
    $cabinet = esc_url(rawlead_page_url('cabinet'));
    return match ($slug) {
        'pricing' => '<h2>ИИ-агент</h2>
<p><strong>790 ₽ / мес</strong> — оплата картой или СБП через ЮKassa.</p>
<p><strong>3 дня Trial — бесплатно и автоматически при первом входе</strong> (1× на аккаунт TG). Далее — <strong>790 ₽/мес</strong> — без автосписания.</p>
<p>Для любой ниши — дизайн, тексты, код, маркетинг. ИИ знает твой профиль из квиза.</p>
<ul>
<li>Персональная лента с % совпадения</li>
<li>Черновик отклика — ИИ пишет, ты правишь. Для каждого — своя формулировка.</li>
<li>5 откликов в час — защита от спама · push в Telegram при матче</li>
</ul>
<p><a href="' . $cabinet . '">Вход в кабинет →</a> · <a href="' . $lenta . '">Смотреть ленту →</a></p>
<p><a class="rl-btn rl-btn--primary" href="' . $cabinet . '">Оформить Premium →</a></p>',
        'how'     => '<h2>1. Проходишь квиз</h2>
<p>Ответь на карточки заказов — RawLead узнает твой профиль. Не нужно вводить навыки вручную.</p>
<h2>2. Настраивается профиль</h2>
<p>Профиль хранит твои предпочтения. Лента автоматически подбирает заказы с % совпадения.</p>
<div class="rl-how-callout">
<h3>ИИ запоминает, что тебе близко — профиль собирается на ходу</h3>
<p>Первый профиль — из квиза. Дальше система смотрит, на что ты откликаешься, и уточняет % совпадения под твой реальный стек. Не нужно ничего настраивать вручную.</p>
</div>
<h2>3. Радар следит 24/7</h2>
<p>Десятки источников проверяются автоматически. Дубликаты, спам и нерелевантные объявления не попадают в ленту.</p>
<h2>4. ИИ читает суть заказа</h2>
<p>Система понимает задачу, решает, что нужно для её выполнения, и сверяет с твоим стеком.</p>
<h2>5. Ты откликаешься сам</h2>
<p>Черновик уже готов — для тебя написан отдельно, не скопирован с чужого отклика. Поправь детали и отправь. Мы не пишем заказчикам за тебя.</p>
<h2>Защита от спама</h2>
<p>Система жёстко контролирует нагрузку: лимит — <strong>5 откликов в час</strong>. Мы защищаем твой аккаунт от спам-фильтров бирж и гарантируем заказчикам качество.</p>
<p><strong>Один поток вместо десятка вкладок.</strong> Premium с персональной лентой и push — от <strong>790 ₽/мес</strong> (ЮKassa).</p>
<p><a class="rl-btn rl-btn--primary" href="' . $cabinet . '">Войти в кабинет →</a></p>',
        'faq'     => rawlead_faq_groups_html($lenta, $cabinet),
        'contact' => rawlead_contact_page_html(),
        default   => null,
    };
}
