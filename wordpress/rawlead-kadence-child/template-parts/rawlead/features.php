<?php
/**
 * Features 01 · 02 · 03 — REFERENCE §3.5
 *
 * @package RawLead_Kadence_Child
 */

declare(strict_types=1);

$items = [
    ['num' => '01', 'title' => __('Один поток', 'rawlead-kadence-child'), 'text' => __('FL + Kwork + TG без переключения вкладок', 'rawlead-kadence-child')],
    ['num' => '02', 'title' => __('ИИ-разбор', 'rawlead-kadence-child'), 'text' => __('брать / сомнительно / пропустить', 'rawlead-kadence-child')],
    ['num' => '03', 'title' => __('Вы решаете', 'rawlead-kadence-child'), 'text' => __('пуш в Telegram, отклик вручную', 'rawlead-kadence-child')],
];
?>
<section class="rl-section rl-features-scroll rl-reveal" aria-labelledby="rl-features-title">
	<div class="rl-container">
		<div class="rl-features-scroll__head">
			<h2 id="rl-features-title"><?php esc_html_e('Как устроено', 'rawlead-kadence-child'); ?></h2>
			<p class="rl-features-scroll__hint"><?php esc_html_e('Свайп влево — следующий шаг', 'rawlead-kadence-child'); ?></p>
		</div>
		<div class="rl-features-track" tabindex="0" role="region" aria-label="<?php esc_attr_e('Функции 01–03', 'rawlead-kadence-child'); ?>">
			<?php foreach ($items as $item) : ?>
				<article class="rl-feature rl-feature--slide">
					<span class="rl-feature__ghost" aria-hidden="true"><?php echo esc_html($item['num']); ?></span>
					<h3 class="rl-feature__title"><?php echo esc_html($item['title']); ?></h3>
					<p class="rl-feature__text"><?php echo esc_html($item['text']); ?></p>
				</article>
			<?php endforeach; ?>
		</div>
	</div>
</section>
