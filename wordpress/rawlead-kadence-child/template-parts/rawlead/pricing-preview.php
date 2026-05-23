<?php
/**
 * Pricing preview — REFERENCE §3.7
 *
 * @package RawLead_Kadence_Child
 */

declare(strict_types=1);

$pricing = rawlead_page_url('pricing');
$contact = rawlead_page_url('contact');

$plans = [
    [
        'name'  => __('Старт', 'rawlead-kadence-child'),
        'price' => __('0 ₽', 'rawlead-kadence-child'),
        'items' => [
            __('1–2 источника (биржи)', 'rawlead-kadence-child'),
            __('Базовые фильтры', 'rawlead-kadence-child'),
            __('Уведомления в Telegram', 'rawlead-kadence-child'),
        ],
        'badge'    => __('Скоро', 'rawlead-kadence-child'),
        'cta'      => __('Подробнее', 'rawlead-kadence-child'),
        'cta_href' => $pricing,
        'featured' => false,
        'btn'      => 'secondary',
    ],
    [
        'name'  => __('Про', 'rawlead-kadence-child'),
        'price' => __('~990 ₽/мес', 'rawlead-kadence-child'),
        'items' => [
            __('FL + Kwork + Telegram-чаты', 'rawlead-kadence-child'),
            __('Свои ключевые слова', 'rawlead-kadence-child'),
            __('ИИ-разбор каждого лида', 'rawlead-kadence-child'),
        ],
        'badge'    => __('Скоро', 'rawlead-kadence-child'),
        'cta'      => __('Ранний доступ', 'rawlead-kadence-child'),
        'cta_href' => $contact,
        'featured' => true,
        'btn'      => 'primary',
    ],
    [
        'name'  => __('Команда', 'rawlead-kadence-child'),
        'price' => __('по запросу', 'rawlead-kadence-child'),
        'items' => [
            __('Несколько исполнителей', 'rawlead-kadence-child'),
            __('Общий пул чатов', 'rawlead-kadence-child'),
            __('Приоритетная поддержка', 'rawlead-kadence-child'),
        ],
        'badge'    => '',
        'cta'      => __('Написать', 'rawlead-kadence-child'),
        'cta_href' => 'https://t.me/rcnn43',
        'featured' => false,
        'btn'      => 'secondary',
    ],
];
?>
<section class="rl-section rl-reveal" aria-labelledby="rl-pricing-title">
	<div class="rl-container">
		<h2 id="rl-pricing-title"><?php esc_html_e('Тарифы', 'rawlead-kadence-child'); ?></h2>
		<div class="rl-pricing">
			<?php foreach ($plans as $plan) : ?>
				<?php
				$card_class = 'rl-price-card';
				if ($plan['featured']) {
					$card_class .= ' rl-price-card--featured';
				}
				$btn_class = 'rl-btn rl-btn--' . $plan['btn'];
				?>
				<article class="<?php echo esc_attr($card_class); ?>">
					<?php if ($plan['featured']) : ?>
						<span class="rl-price-card__ribbon"><?php esc_html_e('Популярный', 'rawlead-kadence-child'); ?></span>
					<?php endif; ?>
					<h3 class="rl-price-card__name"><?php echo esc_html($plan['name']); ?></h3>
					<p class="rl-price-card__price"><?php echo esc_html($plan['price']); ?></p>
					<ul class="rl-price-card__list">
						<?php foreach ($plan['items'] as $li) : ?>
							<li><?php echo esc_html($li); ?></li>
						<?php endforeach; ?>
					</ul>
					<?php if ($plan['badge'] !== '') : ?>
						<span class="rl-price-card__badge"><?php echo esc_html($plan['badge']); ?></span>
					<?php endif; ?>
					<div class="rl-price-card__cta">
						<a class="<?php echo esc_attr($btn_class); ?>" href="<?php echo esc_url($plan['cta_href']); ?>"
							<?php echo str_starts_with($plan['cta_href'], 'https://') ? ' target="_blank" rel="noopener"' : ''; ?>>
							<?php echo esc_html($plan['cta']); ?>
						</a>
					</div>
				</article>
			<?php endforeach; ?>
		</div>
		<p style="margin-top:1.5rem;text-align:center">
			<a class="rl-link-arrow" href="<?php echo esc_url($pricing); ?>"><?php esc_html_e('Все тарифы', 'rawlead-kadence-child'); ?> →</a>
		</p>
	</div>
</section>
