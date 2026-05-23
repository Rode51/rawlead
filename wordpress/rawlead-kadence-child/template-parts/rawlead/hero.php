<?php
/**
 * Hero — REFERENCE §3.2 · wp-skeleton/home.md
 *
 * @package RawLead_Kadence_Child
 */

declare(strict_types=1);

$pricing = rawlead_page_url('pricing');
$how = rawlead_page_url('how');
?>
<section class="rl-hero rl-section rl-reveal" aria-labelledby="rl-hero-title">
	<div class="rl-container rl-hero__grid">
		<div class="rl-hero__copy">
			<h1 id="rl-hero-title" class="rl-hero__title"><?php esc_html_e('Лиды без шума', 'rawlead-kadence-child'); ?></h1>
			<p class="rl-hero__lead">
				<strong><?php esc_html_e('FL.ru, Kwork и Telegram-чаты', 'rawlead-kadence-child'); ?></strong>
				<?php esc_html_e(' — в одном потоке. Фильтры режут спам, ИИ подсказывает, стоит ли писать заказчику.', 'rawlead-kadence-child'); ?>
			</p>
			<div class="rl-hero__actions">
				<a class="rl-btn rl-btn--primary" href="<?php echo esc_url($pricing); ?>"><?php esc_html_e('Смотреть тарифы', 'rawlead-kadence-child'); ?></a>
				<a class="rl-link-arrow" href="<?php echo esc_url($how); ?>"><?php esc_html_e('Как это работает', 'rawlead-kadence-child'); ?> →</a>
			</div>
		</div>
		<?php rawlead_get_part('hero-visual'); ?>
	</div>
</section>
