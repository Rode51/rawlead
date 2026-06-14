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
	__('Персональная лента с % совпадения · push при матче · без задержки', 'rawlead-kadence-child'),
	__('5 откликов в час — защита от спама', 'rawlead-kadence-child'),
];

$bullets_full = array_merge($bullets_preview, [
	__('Пуш в Telegram — только при хорошем совпадении', 'rawlead-kadence-child'),
]);

?>
<article class="rl-price-card rl-price-card--o174<?php echo $is_full ? ' rl-price-card--full' : ' rl-price-card--preview'; ?>">
	<h3 class="rl-price-card__name"><?php esc_html_e('RawLead Premium', 'rawlead-kadence-child'); ?></h3>
	<p class="rl-price-card__price">
		<span class="rl-price-card__price-main"><?php esc_html_e('790 ₽ / мес', 'rawlead-kadence-child'); ?></span>
	</p>
	<p class="rl-price-card__price-secondary">
		<span class="rl-price-card__chip"><?php esc_html_e('первые 3 дня бесплатно', 'rawlead-kadence-child'); ?></span>
	</p>
	<ul class="rl-price-card__list">
		<?php
		$list = $is_full ? $bullets_full : $bullets_preview;
		foreach ($list as $li) :
			?>
			<li><?php echo esc_html($li); ?></li>
		<?php endforeach; ?>
	</ul>
	<?php if ($is_full) : ?>
		<p class="rl-price-card__legal">
			<?php esc_html_e('3 дня Trial — бесплатно и автоматически при первом входе (1× на аккаунт TG). Далее 790 ₽/мес — без автосписания. Оплата картой или СБП через ЮKassa.', 'rawlead-kadence-child'); ?>
		</p>
	<?php endif; ?>
	<div class="rl-price-card__cta">
		<?php if ($is_full) : ?>
			<button type="button" class="rl-btn rl-btn--primary rl-btn--full" id="rl-price-checkout-sub">
				<?php esc_html_e('Оформить Premium →', 'rawlead-kadence-child'); ?>
			</button>
			<p class="rl-price-card__checkout-note" id="rl-price-checkout-note" hidden></p>
			<p class="rl-price-card__cta-secondary">
				<a class="rl-link-arrow" href="<?php echo $lenta; ?>"><?php esc_html_e('Смотреть ленту →', 'rawlead-kadence-child'); ?></a>
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
