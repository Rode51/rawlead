<?php
/**
 * Hero — REFERENCE §3.2 · wp-skeleton/home.md
 *
 * @package RawLead_Kadence_Child
 */

declare(strict_types=1);

$lenta = rawlead_page_url('lenta');
$cabinet = rawlead_page_url('cabinet');
?>
<section class="rl-hero rl-section rl-reveal" aria-labelledby="rl-hero-title">
	<div class="rl-container rl-hero__grid">
		<div class="rl-hero__copy">
			<p class="rl-hero__eyebrow"><?php esc_html_e('RawLead · фриланс-радар', 'rawlead-kadence-child'); ?></p>
			<h1 id="rl-hero-title" class="rl-hero__title">
				<span class="rl-hero__title-line"><?php esc_html_e('Заказы', 'rawlead-kadence-child'); ?></span>
				<span class="rl-hero__title-line rl-hero__title-line--accent"><?php esc_html_e('под ваш стек', 'rawlead-kadence-child'); ?></span>
			</h1>
			<p class="rl-hero__lead">
				<?php esc_html_e('FL.ru, Kwork и Telegram — один поток. Фильтры отсекают шум, ИИ показывает совместимость с вашими навыками.', 'rawlead-kadence-child'); ?>
			</p>
			<div class="rl-hero__actions">
				<a class="rl-btn rl-btn--primary" href="<?php echo esc_url($lenta); ?>"><?php esc_html_e('Смотреть ленту', 'rawlead-kadence-child'); ?></a>
				<a class="rl-btn rl-btn--ghost" href="<?php echo esc_url($cabinet); ?>"><?php esc_html_e('Вход в ЛК', 'rawlead-kadence-child'); ?></a>
				<a class="rl-link-arrow" href="#pricing-preview"><?php esc_html_e('Смотреть тарифы ↓', 'rawlead-kadence-child'); ?></a>
			</div>
		</div>
		<?php rawlead_get_part('hero-visual'); ?>
	</div>
</section>
