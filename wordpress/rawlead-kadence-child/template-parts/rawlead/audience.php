<?php
/**
 * Audience cards — REFERENCE §3.6 · wp-skeleton/home.md
 *
 * @package RawLead_Kadence_Child
 */

declare(strict_types=1);

$cards = [
    __('Разработчики и верстальщики на Cursor / WordPress', 'rawlead-kadence-child'),
    __('Те, кто устал вручную мониторить биржи и чаты', 'rawlead-kadence-child'),
    __('Фрилансеры, которые сами пишут в ЛС (без автоспама)', 'rawlead-kadence-child'),
];
?>
<section class="rl-section rl-section--alt rl-reveal" aria-labelledby="rl-audience-title">
	<div class="rl-container">
		<h2 id="rl-audience-title"><?php esc_html_e('Для кого', 'rawlead-kadence-child'); ?></h2>
		<div class="rl-audience">
			<?php foreach ($cards as $text) : ?>
				<div class="rl-audience-card">
					<p><?php echo esc_html($text); ?></p>
				</div>
			<?php endforeach; ?>
		</div>
	</div>
</section>
