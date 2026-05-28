<?php
/**
 * Pricing preview — REFERENCE §3.7 (single plan)
 *
 * @package RawLead_Kadence_Child
 */

declare(strict_types=1);

$contact = rawlead_page_url('contact');

$plan = [
    'name'     => __('ИИ-агент', 'rawlead-kadence-child'),
    'price'    => __('от 300 ₽/мес', 'rawlead-kadence-child'),
    'subtitle' => __('Для любой ниши — дизайн, тексты, код, маркетинг. ИИ знает ваши теги.', 'rawlead-kadence-child'),
    'items'    => [
        __('Персональная лента по вашим навыкам', 'rawlead-kadence-child'),
        __('ИИ-оценка каждого заказа', 'rawlead-kadence-child'),
        __('Черновик отклика за одну кнопку', 'rawlead-kadence-child'),
        __('Рыночная цена заказа', 'rawlead-kadence-child'),
        __('Push в Telegram при новом матче', 'rawlead-kadence-child'),
    ],
    'badge' => __('Скоро', 'rawlead-kadence-child'),
    'cta'   => __('Узнать первым →', 'rawlead-kadence-child'),
];
?>
<section id="pricing-preview" class="rl-section rl-reveal" aria-labelledby="rl-pricing-title">
	<div class="rl-container">
		<h2 id="rl-pricing-title"><?php esc_html_e('Тариф', 'rawlead-kadence-child'); ?></h2>
		<div class="rl-pricing rl-pricing--single">
			<article class="rl-price-card">
				<span class="rl-price-card__badge"><?php echo esc_html($plan['badge']); ?></span>
				<h3 class="rl-price-card__name"><?php echo esc_html($plan['name']); ?></h3>
				<p class="rl-price-card__price"><?php echo esc_html($plan['price']); ?></p>
				<p class="rl-price-card__lead"><em><?php echo esc_html($plan['subtitle']); ?></em></p>
				<ul class="rl-price-card__list">
					<?php foreach ($plan['items'] as $li) : ?>
						<li><?php echo esc_html($li); ?></li>
					<?php endforeach; ?>
				</ul>
				<div class="rl-price-card__cta">
					<a class="rl-btn rl-btn--primary" href="<?php echo esc_url($contact); ?>">
						<?php echo esc_html($plan['cta']); ?>
					</a>
				</div>
			</article>
		</div>
		<p class="rl-pricing__note">
			<em><?php esc_html_e('Оплата через Telegram Stars — скоро. Сейчас лента и кабинет бесплатно.', 'rawlead-kadence-child'); ?></em>
		</p>
		<p class="rl-pricing__link">
			<a class="rl-link-arrow" href="<?php echo esc_url($contact); ?>"><?php esc_html_e('Узнать первым →', 'rawlead-kadence-child'); ?></a>
		</p>
	</div>
</section>
