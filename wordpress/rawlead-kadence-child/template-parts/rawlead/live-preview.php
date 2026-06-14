<?php
/**
 * Live Preview Feed — static marketing demo (O55a).
 *
 * @package RawLead_Kadence_Child
 */

declare(strict_types=1);

$lenta = rawlead_page_url('lenta');

/**
 * @param array<string, mixed> $card
 */
function rawlead_render_demo_preview_card(array $card, string $lenta_url): void {
	$pct = (int) ($card['pct'] ?? 0);
	$source = (string) ($card['source'] ?? 'fl');
	$source_label = (string) ($card['source_label'] ?? 'FL.ru');
	$title = (string) ($card['title'] ?? '');
	$tags = is_array($card['tags'] ?? null) ? $card['tags'] : [];
	$perfect = !empty($card['perfect']);
	$hero = !empty($card['hero']);

	$classes = ['rl-lead-card', 'is-visible'];
	if ($perfect) {
		$classes[] = 'rl-lead-card--perfect-match';
	}
	if ($hero) {
		$classes[] = 'rl-lead-card--demo-hero';
	}

	$chips = '';
	foreach (array_slice($tags, 0, 4) as $tag) {
		$chips .= '<span class="rl-chip">' . esc_html((string) $tag) . '</span>';
	}
	$extra = count($tags) - 4;
	if ($extra > 0) {
		$chips .= '<span class="rl-chip rl-chip--more">+' . (int) $extra . '</span>';
	}

	$perfect_badge = $perfect
		? '<span class="rl-badge rl-badge--perfect">ИДЕАЛЬНО ✦</span>'
		: '';
	$niche = (string) ($card['category'] ?? '');
	$niche_icons = [
		'dev'       => '</>',
		'design'    => '✦',
		'marketing' => '◎',
		'text'      => 'Aa',
	];
	$niche_icon = '';
	?>
	<article class="<?php echo esc_attr(implode(' ', $classes)); ?>">
		<div class="rl-feed-card__head">
			<div class="rl-feed-card__head-start">
				<?php echo $niche_icon; // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped -- escaped above ?>
				<span class="rl-feed-card__source rl-feed-card__source--<?php echo esc_attr($source); ?>">
					<?php echo esc_html($source_label); ?>
				</span>
				<?php echo $perfect_badge; // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped -- static badge ?>
			</div>
		</div>
		<h3 class="rl-lead-card__title"><?php echo esc_html($title); ?></h3>
		<p class="rl-lead-card__budget"><?php esc_html_e('Бюджет: —', 'rawlead-kadence-child'); ?></p>
		<div class="rl-match">
			<div class="rl-match__label">
				<span><?php echo esc_html(sprintf('Совместимость %d%%', $pct)); ?></span>
			</div>
			<div
				class="rl-match__bar"
				role="progressbar"
				aria-valuenow="<?php echo (int) $pct; ?>"
				aria-valuemin="0"
				aria-valuemax="100"
			>
				<span class="rl-match__fill" style="--match-value:<?php echo (int) $pct; ?>%"></span>
			</div>
		</div>
		<div class="rl-chips"><?php echo $chips; // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped -- esc_html per chip ?></div>
		<div class="rl-live-preview__cta">
			<a class="rl-btn rl-btn--primary" href="<?php echo esc_url($lenta_url); ?>">
				<?php esc_html_e('Написать отклик', 'rawlead-kadence-child'); ?>
			</a>
		</div>
	</article>
	<?php
}

$demo_cards = [
	[
		'pct' => 50,
		'source' => 'fl',
		'source_label' => 'FL.ru',
		'category' => 'dev',
		'title' => 'Доработка CRM под отчёты',
		'tags' => ['PHP', 'MySQL', 'REST API'],
	],
	[
		'pct' => 100,
		'source' => 'tg',
		'source_label' => 'TG',
		'category' => 'dev',
		'title' => 'Интеграция Telegram-бота с CRM',
		'tags' => ['Python', 'REST API', 'PostgreSQL'],
		'perfect' => true,
		'hero' => true,
	],
	[
		'pct' => 80,
		'source' => 'kwork',
		'source_label' => 'Kwork',
		'category' => 'design',
		'title' => 'Лендинг на WordPress + форма',
		'tags' => ['WordPress', 'CSS', 'PHP'],
	],
];
?>
<section class="rl-live-preview" aria-label="<?php esc_attr_e('Последние заказы', 'rawlead-kadence-child'); ?>">
	<div class="rl-container">
		<p class="rl-live-preview__label"><?php esc_html_e('Последние заказы', 'rawlead-kadence-child'); ?></p>
		<div
			class="rl-live-preview__cards rl-live-preview__cards--demo"
			id="rl-live-preview-cards"
			data-lenta-url="<?php echo esc_url($lenta); ?>"
		>
			<?php foreach ($demo_cards as $card) : ?>
				<?php rawlead_render_demo_preview_card($card, $lenta); ?>
			<?php endforeach; ?>
		</div>
		<a class="rl-live-preview__link" href="<?php echo esc_url($lenta); ?>">
			<?php esc_html_e('Открыть все →', 'rawlead-kadence-child'); ?>
		</a>
	</div>
</section>
