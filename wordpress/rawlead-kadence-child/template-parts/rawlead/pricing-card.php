<?php
/**
 * Pricing card — O105 D2 (preview) · D3 (full).
 *
 * Set $rawlead_pricing_variant = 'preview'|'full' before include.
 *
 * @package RawLead_Kadence_Child
 */

declare(strict_types=1);

$variant = isset($rawlead_pricing_variant) && $rawlead_pricing_variant === 'full' ? 'full' : 'preview';
$is_full = $variant === 'full';

$bot_pay = rawlead_bot_pay_url('pay');
$cabinet = esc_url(rawlead_page_url('cabinet'));
$lenta = esc_url(rawlead_page_url('lenta'));
$pricing = esc_url(rawlead_page_url('pricing'));

$bullets_preview = [
    __('Уникальный черновик отклика — ИИ пишет под тебя, ты отправляешь сам', 'rawlead-kadence-child'),
    __('Лента без задержки и push — заказы появляются сразу при match', 'rawlead-kadence-child'),
    __('Пуш в Telegram — только при хорошем совпадении', 'rawlead-kadence-child'),
];

$bullets_full = array_merge($bullets_preview, [
    __('Умный лимит (10 откликов в час) — защита от спам-фильтров бирж', 'rawlead-kadence-child'),
]);

$footnote = __('Лимит в час — защита от случайных кликов (anti-тык)', 'rawlead-kadence-child');

$payment_rows = [
    [
        'icon'  => '💳',
        'label' => __('Банковская карта РФ / СБП — 790 ₽', 'rawlead-kadence-child'),
        'label_mobile' => __('Карта / СБП — 790 ₽', 'rawlead-kadence-child'),
        'start' => 'pay_sbp',
    ],
    [
        'icon'  => '🪙',
        'label' => __('Crypto — USDT (TRC20) или TON', 'rawlead-kadence-child'),
        'label_mobile' => __('Crypto — USDT / TON', 'rawlead-kadence-child'),
        'start' => 'pay_crypto',
    ],
    [
        'icon'  => '⭐',
        'label' => __('Telegram Stars — 600 ⭐ / мес', 'rawlead-kadence-child'),
        'label_mobile' => __('Stars — 600 ⭐ / мес', 'rawlead-kadence-child'),
        'start' => 'pay_stars',
    ],
];

?>
<article class="rl-price-card rl-price-card--o105<?php echo $is_full ? ' rl-price-card--full' : ' rl-price-card--preview'; ?>">
	<h3 class="rl-price-card__name"><?php esc_html_e('RawLead Premium', 'rawlead-kadence-child'); ?></h3>
	<p class="rl-price-card__price">
		<span class="rl-price-card__price-main"><?php esc_html_e('790 ₽ / мес', 'rawlead-kadence-child'); ?></span>
	</p>
	<p class="rl-price-card__price-secondary">
		<?php esc_html_e('или 600 ⭐ Stars в Telegram', 'rawlead-kadence-child'); ?>
	</p>
	<ul class="rl-price-card__list">
		<?php
		$list = $is_full ? $bullets_full : $bullets_preview;
		foreach ($list as $li) :
			?>
			<li><?php echo esc_html($li); ?></li>
		<?php endforeach; ?>
		<?php if ($is_full) : ?>
			<li class="rl-price-card__list-item--muted rl-price-card__list-item--desktop"><?php echo esc_html($footnote); ?></li>
		<?php endif; ?>
	</ul>
	<?php if ($is_full) : ?>
		<p class="rl-price-card__footnote"><?php echo esc_html($footnote); ?></p>
		<div class="rl-payment-block">
			<h4 class="rl-payment-block__title"><?php esc_html_e('Способы оплаты', 'rawlead-kadence-child'); ?></h4>
			<div class="rl-payment-block__rows">
				<?php foreach ($payment_rows as $row) : ?>
					<?php
					$row_pay = rawlead_bot_pay_url($row['start'] ?? 'pay');
					?>
					<a class="rl-payment-row" href="<?php echo $row_pay; ?>" target="_blank" rel="noopener">
						<span class="rl-payment-row__icon" aria-hidden="true"><?php echo esc_html($row['icon']); ?></span>
						<span class="rl-payment-row__label rl-payment-row__label--desktop"><?php echo esc_html($row['label']); ?></span>
						<span class="rl-payment-row__label rl-payment-row__label--mobile"><?php echo esc_html($row['label_mobile']); ?></span>
						<span class="rl-payment-row__chevron" aria-hidden="true">›</span>
					</a>
				<?php endforeach; ?>
			</div>
		</div>
	<?php endif; ?>
	<div class="rl-price-card__cta">
		<a class="rl-btn rl-btn--primary rl-btn--full" href="<?php echo $cabinet; ?>">
			<?php esc_html_e('Подключить Premium →', 'rawlead-kadence-child'); ?>
		</a>
		<?php if ($is_full) : ?>
			<p class="rl-price-card__cta-secondary">
				<a class="rl-link-arrow" href="<?php echo $lenta; ?>"><?php esc_html_e('Продолжить с ограничениями (Free) →', 'rawlead-kadence-child'); ?></a>
			</p>
		<?php endif; ?>
	</div>
	<?php if (!$is_full) : ?>
		<p class="rl-pricing__link">
			<a class="rl-link-arrow" href="<?php echo $pricing; ?>"><?php esc_html_e('Подробнее о тарифе →', 'rawlead-kadence-child'); ?></a>
		</p>
	<?php endif; ?>
</article>
