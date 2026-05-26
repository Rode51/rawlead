<?php
/**
 * Audience cards — REFERENCE §3.6 · vision v0.10 (4 категории Digital)
 *
 * @package RawLead_Kadence_Child
 */

declare(strict_types=1);

$cards = [
    [
        'title' => __('Разработка & Код', 'rawlead-kadence-child'),
        'text'  => __('Боты, парсеры, FastAPI, веб — один поток вместо десятка вкладок.', 'rawlead-kadence-child'),
        'tags'  => __('Python · бот · парсер · автоматизация', 'rawlead-kadence-child'),
    ],
    [
        'title' => __('Дизайн & Видео', 'rawlead-kadence-child'),
        'text'  => __('UI/UX, Reels, монтаж, motion — заказы точно по вашим навыкам, без шума.', 'rawlead-kadence-child'),
        'tags'  => __('Figma · UI · монтаж · анимация', 'rawlead-kadence-child'),
    ],
    [
        'title' => __('Маркетинг & SMM', 'rawlead-kadence-child'),
        'text'  => __('Таргет, SEO, SMM, воронки — ИИ убирает нерелевантное до того, как вы открыли ленту.', 'rawlead-kadence-child'),
        'tags'  => __('таргет · SEO · SMM · контекст', 'rawlead-kadence-child'),
    ],
    [
        'title' => __('Тексты & Переводы', 'rawlead-kadence-child'),
        'text'  => __('Копирайтинг, локализация, редактура — только заказы под ваш профиль.', 'rawlead-kadence-child'),
        'tags'  => __('копирайт · перевод · редактура · субтитры', 'rawlead-kadence-child'),
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
