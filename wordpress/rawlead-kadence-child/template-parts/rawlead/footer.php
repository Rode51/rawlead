<?php
/**
 * Footer — REFERENCE §3.8 · w2-6
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
		<p class="rl-footer__copy">
			<span class="rl-footer__byline"><?php esc_html_e('RawLead · by Rode51', 'rawlead-kadence-child'); ?></span>
			· © <?php echo esc_html((string) $year); ?>
		</p>
	</div>
</footer>
<button type="button" class="rl-support-fab" id="rl-support-fab" aria-label="<?php esc_attr_e('Поддержка', 'rawlead-kadence-child'); ?>">
	<svg width="18" height="18" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true" focusable="false">
		<circle cx="10" cy="10" r="9" stroke="#0A0A0A" stroke-width="2"/>
		<path d="M10 6v5M10 13v1" stroke="#0A0A0A" stroke-width="2" stroke-linecap="round"/>
	</svg>
	<span class="rl-support-fab__label"><?php esc_html_e('Поддержка', 'rawlead-kadence-child'); ?></span>
</button>
<div class="rl-support-modal" id="rl-support-modal" hidden aria-modal="true" role="dialog" aria-labelledby="rl-support-modal-title">
	<div class="rl-support-modal__overlay" id="rl-support-overlay"></div>
	<div class="rl-support-modal__box">
		<div class="rl-support-modal__head">
			<span class="rl-support-modal__title" id="rl-support-modal-title"><?php esc_html_e('Написать в поддержку', 'rawlead-kadence-child'); ?></span>
			<button type="button" class="rl-support-modal__close" id="rl-support-close" aria-label="<?php esc_attr_e('Закрыть', 'rawlead-kadence-child'); ?>">✕</button>
		</div>
		<textarea class="rl-support-modal__input" id="rl-support-text"
			placeholder="<?php esc_attr_e('Опиши, что случилось — URL, что делал(а), что ожидал(а)...', 'rawlead-kadence-child'); ?>"
			rows="5"></textarea>
		<button type="button" class="rl-btn rl-support-modal__submit" id="rl-support-submit"><?php esc_html_e('Отправить →', 'rawlead-kadence-child'); ?></button>
		<div class="rl-support-modal__success" id="rl-support-success" hidden>
			<?php esc_html_e('Получили — ответим в Telegram 🙌', 'rawlead-kadence-child'); ?>
		</div>
	</div>
</div>
