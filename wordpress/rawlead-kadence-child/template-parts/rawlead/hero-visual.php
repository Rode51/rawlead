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
		<svg class="rl-hero-visual__paths" viewBox="0 0 120 80" fill="none" xmlns="http://www.w3.org/2000/svg">
			<path class="rl-hero-visual__path" d="M20 20 C50 20, 55 40, 60 48" stroke="currentColor" stroke-width="1.5" stroke-dasharray="4 4"/>
			<path class="rl-hero-visual__path" d="M60 12 C60 30, 58 40, 60 48" stroke="currentColor" stroke-width="1.5"/>
			<path class="rl-hero-visual__path" d="M100 24 C72 28, 65 40, 60 48" stroke="currentColor" stroke-width="1.5" stroke-dasharray="4 4"/>
			<circle class="rl-hero-visual__dot" cx="60" cy="48" r="4" fill="currentColor"/>
		</svg>
		<article class="rl-hero-visual__card">
			<p class="rl-hero-visual__card-label"><?php esc_html_e('Лид', 'rawlead-kadence-child'); ?></p>
			<h3 class="rl-hero-visual__card-title"><?php esc_html_e('Лендинг на WordPress', 'rawlead-kadence-child'); ?></h3>
			<p class="rl-hero-visual__card-budget">25 000 – 40 000 ₽</p>
			<div class="rl-hero-visual__match">
				<span><?php esc_html_e('Совпадение', 'rawlead-kadence-child'); ?></span>
				<strong>88%</strong>
			</div>
			<div class="rl-hero-visual__bar"><span style="width:88%"></span></div>
			<div class="rl-hero-visual__chips">
				<span class="rl-hero-visual__chip rl-hero-visual__chip--ok"><?php esc_html_e('Брать', 'rawlead-kadence-child'); ?></span>
				<span class="rl-hero-visual__chip"><?php esc_html_e('ИИ', 'rawlead-kadence-child'); ?></span>
			</div>
		</article>
		<div class="rl-hero-visual__orbit rl-hero-visual__orbit--1"></div>
		<div class="rl-hero-visual__orbit rl-hero-visual__orbit--2"></div>
	</div>
</div>
