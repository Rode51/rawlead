<?php
/**
 * Hero — REFERENCE §3.2 · WAVE-4-ADDON
 *
 * @package RawLead_Kadence_Child
 */

declare(strict_types=1);

$lenta = rawlead_page_url('lenta');
$geo_svg = RAWLEAD_CHILD_DIR . '/assets/images/wave2-hero-geo-corner-v1.svg';
?>
<section class="rl-hero rl-section rl-reveal" aria-labelledby="rl-hero-title">
	<?php if (is_readable($geo_svg)) : ?>
	<div class="rl-hero__geo" aria-hidden="true">
		<?php // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped -- inline SVG asset
		echo file_get_contents($geo_svg); ?>
	</div>
	<?php endif; ?>
	<div class="rl-hero__floats" aria-hidden="true">
		<div class="rl-hero__float rl-hero__float--1">
			<span class="rl-badge rl-badge--source rl-badge--fl">FL.ru</span>
			<span class="rl-hero__float-title"><?php esc_html_e('Парсинг сайта на Python', 'rawlead-kadence-child'); ?></span>
			<span class="rl-hero__float-budget">4 200 ₽</span>
		</div>
		<div class="rl-hero__float rl-hero__float--2">
			<span class="rl-badge rl-badge--source rl-badge--kwork">Kwork</span>
			<span class="rl-hero__float-title"><?php esc_html_e('Верстка лендинга', 'rawlead-kadence-child'); ?></span>
			<span class="rl-hero__float-budget">3 500 ₽</span>
		</div>
		<div class="rl-hero__float rl-hero__float--3 rl-hero__float--perfect">
			<span class="rl-badge rl-badge--perfect">ИДЕАЛЬНО ✦</span>
			<span class="rl-hero__float-match"><?php esc_html_e('100% совпадение', 'rawlead-kadence-child'); ?></span>
		</div>
	</div>
	<div class="rl-hero__inner">
		<h1 id="rl-hero-title" class="rl-hero__title"><?php esc_html_e('Заказы под твой стек. Без мусора.', 'rawlead-kadence-child'); ?></h1>
		<p class="rl-hero__sub">
			<?php esc_html_e('Умный радар фриланса. ИИ находит идеальные совпадения по твоим навыкам и готовит черновик отклика.', 'rawlead-kadence-child'); ?>
		</p>
		<div class="rl-hero__cta-group">
			<a class="rl-btn rl-btn--primary" href="<?php echo esc_url($lenta); ?>"><?php esc_html_e('Смотреть ленту →', 'rawlead-kadence-child'); ?></a>
			<a class="rl-btn rl-btn--secondary" href="#pricing-preview"><?php esc_html_e('Тарифы ↓', 'rawlead-kadence-child'); ?></a>
		</div>
	</div>
</section>
<?php rawlead_get_part('live-preview'); ?>
<div class="rl-skills-marquee" aria-hidden="true">
	<div class="rl-skills-marquee__track">
		<?php
		$skills = ['Python', 'WordPress', 'React', 'Figma', 'SEO', 'Laravel', 'Telegram Bot', 'UI/UX', 'Копирайтинг', 'Node.js', 'PHP', 'Таргет'];
		foreach (array_merge($skills, $skills, $skills, $skills) as $skill) :
			?>
			<span class="rl-chip"><?php echo esc_html($skill); ?></span>
		<?php endforeach; ?>
	</div>
</div>
