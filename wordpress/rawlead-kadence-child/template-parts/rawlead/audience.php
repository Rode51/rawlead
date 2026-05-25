<?php
/**
 * Audience cards — REFERENCE §3.6 · wp-skeleton/home.md
 *
 * @package RawLead_Kadence_Child
 */

declare(strict_types=1);

$cards = [
    [
        'title' => __('Дизайн и визуал', 'rawlead-kadence-child'),
        'text'  => __('Логотипы, UI/UX, иллюстрации, видеомонтаж — заказы точно по вашим навыкам, без шума дизайн-чатов.', 'rawlead-kadence-child'),
        'tags'  => __('дизайн · UI · иллюстрация · видео', 'rawlead-kadence-child'),
    ],
    [
        'title' => __('Тексты и маркетинг', 'rawlead-kadence-child'),
        'text'  => __('Копирайт, SMM, таргет, переводы, SEO — ИИ убирает нерелевантное ещё до того, как вы открыли ленту.', 'rawlead-kadence-child'),
        'tags'  => __('копирайт · SMM · таргет · SEO', 'rawlead-kadence-child'),
    ],
    [
        'title' => __('Разработка и автоматизация', 'rawlead-kadence-child'),
        'text'  => __('Сайты, боты, скрипты, интеграции — один поток вместо десятка вкладок.', 'rawlead-kadence-child'),
        'tags'  => __('разработка · бот · автоматизация', 'rawlead-kadence-child'),
    ],
];
?>
<section class="rl-section rl-section--alt rl-reveal" aria-labelledby="rl-audience-title">
	<div class="rl-container">
		<h2 id="rl-audience-title"><?php esc_html_e('Для кого', 'rawlead-kadence-child'); ?></h2>
		<div class="rl-audience">
			<?php foreach ($cards as $card) : ?>
				<div class="rl-audience-card">
					<h3 class="rl-audience-card__title"><?php echo esc_html($card['title']); ?></h3>
					<p class="rl-audience-card__text"><?php echo esc_html($card['text']); ?></p>
					<p class="rl-audience-card__tags"><?php echo esc_html($card['tags']); ?></p>
				</div>
			<?php endforeach; ?>
		</div>
	</div>
</section>
