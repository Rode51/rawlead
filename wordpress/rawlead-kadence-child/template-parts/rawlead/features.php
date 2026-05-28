<?php
/**
 * Features 01 · 02 · 03 — REFERENCE §3.5
 *
 * @package RawLead_Kadence_Child
 */

declare(strict_types=1);

$items = [
    [
        'title' => __('Один поток', 'rawlead-kadence-child'),
        'text'  => __('Биржи, агрегаторы, Telegram-каналы — всё в одной ленте. Не нужно переключаться между вкладками и чатами.', 'rawlead-kadence-child'),
    ],
    [
        'title' => __('ИИ-разбор', 'rawlead-kadence-child'),
        'text'  => __('Каждый заказ оценивается до того, как вы его видите. Шлак, спам, реферальные схемы — не доходят до ленты.', 'rawlead-kadence-child'),
    ],
    [
        'title' => __('Вы решаете', 'rawlead-kadence-child'),
        'text'  => __('Подходящий заказ — пуш в Telegram. Откликаетесь сами. Мы не пишем заказчикам за вас.', 'rawlead-kadence-child'),
    ],
];
?>
<section class="rl-section rl-features-scroll rl-reveal" aria-labelledby="rl-features-title">
	<div class="rl-container">
		<div class="rl-features-scroll__head">
			<h2 id="rl-features-title"><?php esc_html_e('Как устроено', 'rawlead-kadence-child'); ?></h2>
		</div>
		<div class="rl-features-track">
			<?php foreach ($items as $item) : ?>
				<article class="rl-feature">
					<h3 class="rl-feature__title"><?php echo esc_html($item['title']); ?></h3>
					<p class="rl-feature__text"><?php echo esc_html($item['text']); ?></p>
				</article>
			<?php endforeach; ?>
		</div>
	</div>
</section>
