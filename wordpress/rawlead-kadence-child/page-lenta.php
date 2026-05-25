<?php
/**
 * Template: /lenta — открытая лента заказов.
 * Slug «feed» в WP зарезервирован под RSS — страница только «lenta».
 *
 * @package RawLead_Kadence_Child
 */

declare(strict_types=1);

get_header();
rawlead_get_part('header');
?>
<main id="primary" class="rl-app rl-app--feed site-main" data-rl-app="feed">
	<div class="rl-container rl-app__layout">
		<aside class="rl-feed-sidebar" id="rl-feed-sidebar" aria-label="<?php esc_attr_e('Фильтры', 'rawlead-kadence-child'); ?>">
			<div class="rl-feed-sidebar__scroll" id="rl-feed-sidebar-scroll">
				<h2 class="rl-feed-sidebar__title"><?php esc_html_e('Фильтры', 'rawlead-kadence-child'); ?></h2>
				<fieldset class="rl-feed-filter">
					<legend><?php esc_html_e('Источник', 'rawlead-kadence-child'); ?></legend>
					<label class="rl-feed-chip is-active"><input type="radio" name="source" value="" checked> <?php esc_html_e('Все', 'rawlead-kadence-child'); ?></label>
					<label class="rl-feed-chip"><input type="radio" name="source" value="fl"> FL.ru</label>
					<label class="rl-feed-chip"><input type="radio" name="source" value="kwork"> Kwork</label>
					<label class="rl-feed-chip"><input type="radio" name="source" value="tg"> Telegram</label>
				</fieldset>
				<fieldset class="rl-feed-filter">
					<legend><?php esc_html_e('ИИ-оценка', 'rawlead-kadence-child'); ?></legend>
					<label class="rl-feed-chip is-active"><input type="radio" name="min_score" value="0" checked> <?php esc_html_e('Любая', 'rawlead-kadence-child'); ?></label>
					<label class="rl-feed-chip"><input type="radio" name="min_score" value="70"> <?php esc_html_e('Брать (≥70)', 'rawlead-kadence-child'); ?></label>
					<label class="rl-feed-chip"><input type="radio" name="min_score" value="85"> <?php esc_html_e('Уверенно (≥85)', 'rawlead-kadence-child'); ?></label>
				</fieldset>
				<details class="rl-feed-filter rl-feed-skills-dd">
					<summary class="rl-feed-skills-dd__trigger">
						<?php esc_html_e('Навыки', 'rawlead-kadence-child'); ?>
						<span class="rl-feed-skills-dd__badge" id="rl-feed-skills-badge" hidden></span>
					</summary>
					<div class="rl-feed-skills-dd__panel" id="rl-feed-skills-panel">
						<p class="rl-feed-skills__lead"><?php esc_html_e('Отметьте, что умеете — лента подстроится', 'rawlead-kadence-child'); ?></p>
						<div class="rl-feed-skills" id="rl-feed-skills" aria-live="polite"></div>
						<p class="rl-feed-skills__hint" id="rl-feed-skills-hint" hidden><?php esc_html_e('Выберите навыки и нажмите Применить', 'rawlead-kadence-child'); ?></p>
						<button type="button" class="rl-btn rl-btn--primary rl-feed-skills-apply" id="rl-feed-skills-apply"><?php esc_html_e('Применить', 'rawlead-kadence-child'); ?></button>
					</div>
				</details>
				<fieldset class="rl-feed-filter">
					<legend><?php esc_html_e('Сортировка', 'rawlead-kadence-child'); ?></legend>
					<label class="rl-feed-chip is-active"><input type="radio" name="sort" value="time" checked> <?php esc_html_e('Новые', 'rawlead-kadence-child'); ?></label>
					<label class="rl-feed-chip"><input type="radio" name="sort" value="match"> <?php esc_html_e('По совместимости', 'rawlead-kadence-child'); ?></label>
				</fieldset>
				<button type="button" class="rl-feed-reset rl-link-arrow" hidden><?php esc_html_e('Сбросить фильтры', 'rawlead-kadence-child'); ?></button>
			</div>
		</aside>
		<div class="rl-feed-main">
			<header class="rl-feed-head">
				<h1 class="rl-feed-head__title"><?php esc_html_e('Лента заказов', 'rawlead-kadence-child'); ?></h1>
				<p class="rl-feed-head__count" id="rl-feed-count" aria-live="polite"></p>
				<button type="button" class="rl-btn rl-btn--ghost rl-feed-filters-btn" id="rl-feed-filters-open" aria-expanded="false">
					<?php esc_html_e('Фильтры', 'rawlead-kadence-child'); ?>
				</button>
			</header>
			<div class="rl-feed-banner" id="rl-feed-error" role="alert" hidden></div>
			<div class="rl-feed-list" id="rl-feed-list" aria-live="polite"></div>
			<div class="rl-feed-sentinel" id="rl-feed-sentinel" aria-hidden="true"></div>
			<p class="rl-feed-end" id="rl-feed-end" hidden><?php esc_html_e('Все заказы загружены', 'rawlead-kadence-child'); ?></p>
		</div>
	</div>
	<div class="rl-feed-sheet" id="rl-feed-sheet" hidden>
		<div class="rl-feed-sheet__overlay" id="rl-feed-sheet-overlay"></div>
		<div class="rl-feed-sheet__panel" role="dialog" aria-modal="true" aria-label="<?php esc_attr_e('Фильтры', 'rawlead-kadence-child'); ?>">
			<div class="rl-feed-sheet__body" id="rl-feed-sheet-body"></div>
			<div class="rl-feed-sheet__actions">
				<button type="button" class="rl-btn rl-btn--primary" id="rl-feed-sheet-apply"><?php esc_html_e('Применить', 'rawlead-kadence-child'); ?></button>
				<button type="button" class="rl-btn rl-btn--ghost" id="rl-feed-sheet-reset"><?php esc_html_e('Сбросить', 'rawlead-kadence-child'); ?></button>
			</div>
		</div>
	</div>
</main>
<?php
rawlead_get_part('footer');
get_footer();
