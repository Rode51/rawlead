<?php
/**
 * Pricing card — O174b YooKassa-only (preview + full).
 *
 * Set $rawlead_pricing_variant = 'preview'|'full' before include.
 *
 * @package RawLead_Kadence_Child
 */

declare(strict_types=1);

$variant = isset($rawlead_pricing_variant) && $rawlead_pricing_variant === 'full' ? 'full' : 'preview';
$is_full = $variant === 'full';

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

?>
<article class="rl-price-card rl-price-card--o174<?php echo $is_full ? ' rl-price-card--full' : ' rl-price-card--preview'; ?>">
	<h3 class="rl-price-card__name"><?php esc_html_e('RawLead Premium', 'rawlead-kadence-child'); ?></h3>
	<p class="rl-price-card__price">
		<span class="rl-price-card__price-main"><?php esc_html_e('790 ₽ / мес', 'rawlead-kadence-child'); ?></span>
	</p>
	<p class="rl-price-card__price-secondary">
		<?php esc_html_e('Попробовать — 1 ₽ / 3 дня (один раз)', 'rawlead-kadence-child'); ?>
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
		<p class="rl-price-card__legal">
			<?php esc_html_e('Оплата картой или СБП через ЮKassa. Trial — 1 ₽ / 3 дня, далее 790 ₽/мес.', 'rawlead-kadence-child'); ?>
		</p>
	<?php endif; ?>
	<div class="rl-price-card__cta">
		<?php if ($is_full) : ?>
			<button type="button" class="rl-btn rl-btn--primary rl-btn--full" id="rl-price-checkout-sub">
				<?php esc_html_e('Оформить Premium →', 'rawlead-kadence-child'); ?>
			</button>
			<button type="button" class="rl-btn rl-btn--ghost rl-btn--full rl-price-card__trial-btn" id="rl-price-checkout-trial">
				<?php esc_html_e('Попробовать за 1 ₽ →', 'rawlead-kadence-child'); ?>
			</button>
			<p class="rl-price-card__checkout-note" id="rl-price-checkout-note" hidden></p>
			<p class="rl-price-card__cta-secondary">
				<a class="rl-link-arrow" href="<?php echo $lenta; ?>"><?php esc_html_e('Продолжить с ограничениями (Free) →', 'rawlead-kadence-child'); ?></a>
			</p>
		<?php else : ?>
			<a class="rl-btn rl-btn--primary rl-btn--full" href="<?php echo $pricing; ?>">
				<?php esc_html_e('Смотреть тарифы →', 'rawlead-kadence-child'); ?>
			</a>
		<?php endif; ?>
	</div>
	<?php if (!$is_full) : ?>
		<p class="rl-pricing__link">
			<a class="rl-link-arrow" href="<?php echo $pricing; ?>"><?php esc_html_e('Подробнее о тарифе →', 'rawlead-kadence-child'); ?></a>
		</p>
	<?php endif; ?>
</article>
