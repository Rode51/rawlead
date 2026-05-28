<?php
/**
 * Hero decorative graphic — sources → lead card (CSS only).
 *
 * @package RawLead_Kadence_Child
 */

declare(strict_types=1);
?>
<div class="rl-hero-visual" aria-hidden="true">
	<div class="rl-hero-visual__glow"></div>
	<div class="rl-hero-visual__grid"></div>
	<div class="rl-hero-visual__panel">
		<div class="rl-hero-visual__sources">
			<span class="rl-hero-visual__pill rl-hero-visual__pill--fl">FL.ru</span>
			<span class="rl-hero-visual__pill rl-hero-visual__pill--kwork">Kwork</span>
			<span class="rl-hero-visual__pill rl-hero-visual__pill--tg">Telegram</span>
		</div>
		<div class="rl-hero-visual__flow" aria-hidden="true">
			<span class="rl-hero-visual__flow-line"></span>
			<span class="rl-hero-visual__flow-node"></span>
		</div>
		<article class="rl-hero-visual__card">
			<p class="rl-hero-visual__card-label"><?php esc_html_e('Лид', 'rawlead-kadence-child'); ?></p>
			<h3 class="rl-hero-visual__card-title"><?php esc_html_e('Лендинг на WordPress', 'rawlead-kadence-child'); ?></h3>
			<p class="rl-hero-visual__card-budget">25 000 – 40 000 ₽</p>
			<div class="rl-hero-visual__match">
				<span><?php esc_html_e('Совместимость', 'rawlead-kadence-child'); ?></span>
				<strong>88%</strong>
			</div>
			<div class="rl-hero-visual__bar"><span style="width:88%"></span></div>
			<div class="rl-hero-visual__chips">
				<span class="rl-hero-visual__chip rl-hero-visual__chip--ok"><?php esc_html_e('Брать', 'rawlead-kadence-child'); ?></span>
				<span class="rl-hero-visual__chip"><?php esc_html_e('ИИ', 'rawlead-kadence-child'); ?></span>
			</div>
		</article>
	</div>
</div>
