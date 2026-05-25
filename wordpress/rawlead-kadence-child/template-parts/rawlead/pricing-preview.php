<?php
/**
 * Pricing preview — REFERENCE §3.7 (single plan)
 *
 * @package RawLead_Kadence_Child
 */

declare(strict_types=1);

$contact = rawlead_page_url('contact');

$plan = [
    'name'  => __('ИИ-агент', 'rawlead-kadence-child'),
    'price' => __('от 300 ₽/мес', 'rawlead-kadence-child'),
    'items' => [
        __('Match по тегам', 'rawlead-kadence-child'),
        __('Рыночная цена', 'rawlead-kadence-child'),
        __('Черновик отклика', 'rawlead-kadence-child'),
        __('Push в TG', 'rawlead-kadence-child'),
    ],
    'badge' => __('Скоро', 'rawlead-kadence-child'),
    'cta'   => __('Ранний доступ', 'rawlead-kadence-child'),
];
?>
<section class="rl-section rl-reveal" aria-labelledby="rl-pricing-title">
	<div class="rl-container">
		<h2 id="rl-pricing-title"><?php esc_html_e('Тариф', 'rawlead-kadence-child'); ?></h2>
		<div class="rl-pricing rl-pricing--single">
			<article class="rl-price-card">
				<span class="rl-price-card__badge"><?php echo esc_html($plan['badge']); ?></span>
				<h3 class="rl-price-card__name"><?php echo esc_html($plan['name']); ?></h3>
				<p class="rl-price-card__price"><?php echo esc_html($plan['price']); ?></p>
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
		<p style="margin-top:1.5rem;text-align:center">
			<a class="rl-link-arrow" href="<?php echo esc_url($contact); ?>"><?php esc_html_e('Связаться →', 'rawlead-kadence-child'); ?></a>
		</p>
	</div>
</section>
