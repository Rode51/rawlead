<?php
/**
 * Template: /pricing — O105 D3 full pricing card.
 *
 * @package RawLead_Kadence_Child
 */

declare(strict_types=1);

get_header();
rawlead_get_part('header');
?>
<main id="primary" class="rl-inner site-main">
	<article class="rl-inner-article page-pricing">
		<header class="rl-inner-hero">
			<div class="rl-container">
				<p class="rl-inner-hero__eyebrow">RawLead</p>
				<h1 class="rl-inner-hero__title"><?php esc_html_e('Тарифы', 'rawlead-kadence-child'); ?></h1>
				<p class="rl-inner-hero__lead"><?php esc_html_e('Пробуй 3 дня бесплатно — автоматически при первом входе.', 'rawlead-kadence-child'); ?></p>
			</div>
		</header>
		<div class="rl-container rl-inner-body rl-pricing-page">
			<div class="rl-pricing rl-pricing--single">
				<?php
				rawlead_get_part('pricing-card', ['rawlead_pricing_variant' => 'full']);
				?>
			</div>
		</div>
	</article>
</main>
<?php
rawlead_get_part('footer');
get_footer();
