<?php
/**
 * Hero — REFERENCE §3.2 · wp-skeleton/home.md
 *
 * @package RawLead_Kadence_Child
 */

declare(strict_types=1);

$lenta = rawlead_page_url('lenta');
?>
<section class="rl-hero rl-section rl-reveal" aria-labelledby="rl-hero-title">
	<div class="rl-container rl-hero__grid">
		<div class="rl-hero__copy">
			<h1 id="rl-hero-title" class="rl-hero__title"><?php esc_html_e('Лиды без шума', 'rawlead-kadence-child'); ?></h1>
			<p class="rl-hero__lead">
				<?php esc_html_e('Биржи, агрегаторы, Telegram-каналы — в одном потоке.', 'rawlead-kadence-child'); ?>
			</p>
			<p class="rl-hero__lead">
				<?php esc_html_e('ИИ выбирает только то, что подходит вашим навыкам.', 'rawlead-kadence-child'); ?>
			</p>
			<div class="rl-hero__actions">
				<a class="rl-btn rl-btn--primary" href="<?php echo esc_url($lenta); ?>"><?php esc_html_e('Смотреть ленту', 'rawlead-kadence-child'); ?></a>
				<a class="rl-link-arrow" href="#pricing-preview"><?php esc_html_e('Смотреть тарифы ↓', 'rawlead-kadence-child'); ?></a>
			</div>
		</div>
		<?php rawlead_get_part('hero-visual'); ?>
	</div>
</section>
