<?php
/**
 * Footer — REFERENCE §3.8
 *
 * @package RawLead_Kadence_Child
 */

declare(strict_types=1);

$year = (int) gmdate('Y');
?>
<footer class="rl-footer" role="contentinfo">
	<div class="rl-container rl-footer__grid">
		<a class="rl-footer__brand" href="<?php echo esc_url(home_url('/')); ?>">RawLead</a>
		<ul class="rl-footer__links">
			<li><a href="<?php echo esc_url(rawlead_page_url('lenta')); ?>"><?php esc_html_e('Лента', 'rawlead-kadence-child'); ?></a></li>
			<li><a href="<?php echo esc_url(rawlead_page_url('cabinet')); ?>"><?php esc_html_e('Кабинет', 'rawlead-kadence-child'); ?></a></li>
			<li><a href="<?php echo esc_url(rawlead_page_url('how')); ?>"><?php esc_html_e('Как работает', 'rawlead-kadence-child'); ?></a></li>
			<li><a href="<?php echo esc_url(rawlead_page_url('pricing')); ?>"><?php esc_html_e('Тарифы', 'rawlead-kadence-child'); ?></a></li>
			<li><a href="<?php echo esc_url(rawlead_page_url('faq')); ?>"><?php esc_html_e('Вопросы', 'rawlead-kadence-child'); ?></a></li>
			<li><a href="<?php echo esc_url(rawlead_page_url('contact')); ?>"><?php esc_html_e('Контакты', 'rawlead-kadence-child'); ?></a></li>
			<li><a href="https://t.me/rcnn43" target="_blank" rel="noopener">Telegram @rcnn43</a></li>
		</ul>
		<p class="rl-footer__copy">© <?php echo esc_html((string) $year); ?> RawLead</p>
	</div>
</footer>
