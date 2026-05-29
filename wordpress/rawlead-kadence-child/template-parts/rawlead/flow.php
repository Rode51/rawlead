<?php
/**
 * Flow block — REFERENCE §3.3 · W13 (sources removed)
 *
 * @package RawLead_Kadence_Child
 */

declare(strict_types=1);
?>
<section class="rl-flow rl-section rl-reveal" aria-labelledby="rl-flow-title">
	<div class="rl-container">
		<h2 id="rl-flow-title" class="rl-flow__title"><?php esc_html_e('Один поток вместо десяти вкладок', 'rawlead-kadence-child'); ?></h2>
		<div class="rl-flow__grid">
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
				<a class="rl-btn rl-btn--ghost" href="<?php echo esc_url(rawlead_page_url('lenta')); ?>"><?php esc_html_e('откликнуться', 'rawlead-kadence-child'); ?></a>
			</article>
		</div>
		<p class="rl-flow__caption"><?php esc_html_e('Биржи и чаты — в одном потоке.', 'rawlead-kadence-child'); ?></p>
	</div>
</section>
