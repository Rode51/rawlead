<?php
/**
 * Flow block — REFERENCE §3.3
 *
 * @package RawLead_Kadence_Child
 */

declare(strict_types=1);
?>
<section class="rl-flow rl-section rl-reveal" aria-labelledby="rl-flow-title">
	<div class="rl-container">
		<h2 id="rl-flow-title" class="rl-flow__title"><?php esc_html_e('Один поток вместо десяти вкладок', 'rawlead-kadence-child'); ?></h2>
		<div class="rl-flow__grid">
			<div class="rl-flow__sources" role="list" aria-label="<?php esc_attr_e('Источники лидов', 'rawlead-kadence-child'); ?>">
				<div class="rl-source-cube rl-source-cube--fl" role="listitem">
					<span class="rl-source-cube__name">FL.ru</span>
				</div>
				<div class="rl-source-cube rl-source-cube--kwork" role="listitem">
					<span class="rl-source-cube__name">Kwork</span>
				</div>
				<div class="rl-source-cube rl-source-cube--tg" role="listitem">
					<span class="rl-source-cube__name">Telegram</span>
				</div>
			</div>
			<div class="rl-flow__arrow" aria-hidden="true">
				<svg width="56" height="32" viewBox="0 0 56 32" fill="none" xmlns="http://www.w3.org/2000/svg">
					<path d="M4 16h40M36 8l8 8-8 8" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
				</svg>
			</div>
			<article class="rl-lead-card">
				<h3 class="rl-lead-card__title"><?php esc_html_e('Верстка лендинга на WordPress', 'rawlead-kadence-child'); ?></h3>
				<p class="rl-lead-card__budget"><?php esc_html_e('Бюджет: 25 000 – 40 000 ₽', 'rawlead-kadence-child'); ?></p>
				<div class="rl-match">
					<div class="rl-match__label">
						<span><?php esc_html_e('Совпадение', 'rawlead-kadence-child'); ?></span>
						<span><strong>88%</strong></span>
					</div>
					<div class="rl-match__bar" role="progressbar" aria-valuenow="88" aria-valuemin="0" aria-valuemax="100" aria-label="<?php esc_attr_e('Совпадение 88%', 'rawlead-kadence-child'); ?>">
						<span class="rl-match__fill" style="--match-value: 88%"></span>
					</div>
				</div>
				<div class="rl-chips">
					<span class="rl-chip rl-chip--take"><?php esc_html_e('Брать', 'rawlead-kadence-child'); ?></span>
					<span class="rl-chip rl-chip--maybe"><?php esc_html_e('ИИ: уверенно', 'rawlead-kadence-child'); ?></span>
				</div>
				<a class="rl-btn rl-btn--ghost" href="<?php echo esc_url(rawlead_page_url('how')); ?>"><?php esc_html_e('Откликнуться сами', 'rawlead-kadence-child'); ?></a>
			</article>
		</div>
		<p class="rl-flow__caption"><?php esc_html_e('Биржи и чаты в одном потоке', 'rawlead-kadence-child'); ?></p>
	</div>
</section>
