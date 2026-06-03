<?php
/**
 * Pricing preview — REFERENCE §3.7 · O105 D2 (#pricing-preview on /)
 *
 * @package RawLead_Kadence_Child
 */

declare(strict_types=1);
?>
<section id="pricing-preview" class="rl-section rl-reveal" aria-labelledby="rl-pricing-title">
	<div class="rl-container">
		<h2 id="rl-pricing-title"><?php esc_html_e('Тариф', 'rawlead-kadence-child'); ?></h2>
		<div class="rl-pricing rl-pricing--single">
			<?php
			rawlead_get_part('pricing-card', ['rawlead_pricing_variant' => 'preview']);
			?>
		</div>
	</div>
</section>
