<?php
/**
 * Filter Bar v2 — unified chrome (O127) · data-tier anon|free|premium.
 *
 * @package RawLead_Kadence_Child
 */

declare(strict_types=1);

$rl_feed_logged_in = isset($rl_feed_logged_in) ? (bool) $rl_feed_logged_in : false;
$rl_feed_tier = isset($rl_feed_tier) ? (string) $rl_feed_tier : ($rl_feed_logged_in ? 'free' : 'anon');
$cabinet_login = esc_url(rawlead_cabinet_login_url());
?>
<div
	class="rl-filter-bar"
	id="rl-feed-sidebar"
	data-tier="<?php echo esc_attr($rl_feed_tier); ?>"
	aria-label="<?php esc_attr_e('Фильтры', 'rawlead-kadence-child'); ?>"
>
	<div class="rl-filter-bar__inner" id="rl-feed-sidebar-scroll">
		<fieldset class="rl-feed-filter rl-feed-filter--source is-visually-hidden">
			<legend><?php esc_html_e('Источник', 'rawlead-kadence-child'); ?></legend>
			<label class="rl-feed-chip"><input type="checkbox" name="source" value="fl"> FL.ru</label>
			<label class="rl-feed-chip"><input type="checkbox" name="source" value="kwork"> Kwork</label>
			<label class="rl-feed-chip"><input type="checkbox" name="source" value="youdo"> YouDo</label>
			<label class="rl-feed-chip"><input type="checkbox" name="source" value="freelance_ru"> Freelance.ru</label>
			<label class="rl-feed-chip"><input type="checkbox" name="source" value="freelancejob"> FreelanceJob</label>
			<label class="rl-feed-chip"><input type="checkbox" name="source" value="pchyol"> Пчёл.нет</label>
			<label class="rl-feed-chip"><input type="checkbox" name="source" value="tg"> Telegram</label>
		</fieldset>
		<div class="rl-filter-bar__chips">
			<fieldset class="rl-feed-filter rl-feed-filter--category rl-filter-bar__cats">
				<legend class="screen-reader-text"><?php esc_html_e('Специализация', 'rawlead-kadence-child'); ?></legend>
				<label class="rl-cat-chip is-active" id="filter-category-all">
					<input type="checkbox" name="category" value="" checked>
					<?php esc_html_e('Все', 'rawlead-kadence-child'); ?>
				</label>
				<label class="rl-cat-chip" id="filter-category-dev">
					<input type="checkbox" name="category" value="dev">
					<span class="rl-cat-chip__icon" aria-hidden="true">&lt;/&gt;</span>
					<span class="rl-cat-chip__label rl-cat-chip__label--full"><?php esc_html_e('Разработка', 'rawlead-kadence-child'); ?></span>
					<span class="rl-cat-chip__label rl-cat-chip__label--short"><?php esc_html_e('Код', 'rawlead-kadence-child'); ?></span>
				</label>
				<label class="rl-cat-chip" id="filter-category-design">
					<input type="checkbox" name="category" value="design">
					<span class="rl-cat-chip__icon" aria-hidden="true">✦</span>
					<span class="rl-cat-chip__label rl-cat-chip__label--full"><?php esc_html_e('Дизайн', 'rawlead-kadence-child'); ?></span>
					<span class="rl-cat-chip__label rl-cat-chip__label--short"><?php esc_html_e('Дизайн', 'rawlead-kadence-child'); ?></span>
				</label>
				<label class="rl-cat-chip" id="filter-category-marketing">
					<input type="checkbox" name="category" value="marketing">
					<span class="rl-cat-chip__icon" aria-hidden="true">
						<svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
							<path d="M3 6.5L8 3v10L3 9.5V6.5z" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/>
							<path d="M8 5l5 2v4l-5 2V5z" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/>
						</svg>
					</span>
					<span class="rl-cat-chip__label rl-cat-chip__label--full"><?php esc_html_e('Маркетинг', 'rawlead-kadence-child'); ?></span>
					<span class="rl-cat-chip__label rl-cat-chip__label--short"><?php esc_html_e('SMM', 'rawlead-kadence-child'); ?></span>
				</label>
				<label class="rl-cat-chip" id="filter-category-text">
					<input type="checkbox" name="category" value="text">
					<span class="rl-cat-chip__icon" aria-hidden="true">Aa</span>
					<span class="rl-cat-chip__label rl-cat-chip__label--full"><?php esc_html_e('Тексты', 'rawlead-kadence-child'); ?></span>
					<span class="rl-cat-chip__label rl-cat-chip__label--short"><?php esc_html_e('Тексты', 'rawlead-kadence-child'); ?></span>
				</label>
			</fieldset>
		</div>
		<div class="rl-filter-bar__actions">
			<button
				type="button"
				class="rl-filter-btn rl-filter-dropdown-btn<?php echo $rl_feed_tier === 'anon' ? ' rl-filter-btn--locked' : ''; ?>"
				id="rl-feed-skills-trigger"
				<?php echo $rl_feed_tier === 'anon' ? ' data-filter-locked="skills"' : ''; ?>
			>
				<span class="rl-filter-btn__label" id="rl-feed-skills-trigger-label"><?php esc_html_e('Навыки', 'rawlead-kadence-child'); ?></span>
				<span class="rl-filter-btn__badge rl-feed-skills-dd__badge" id="rl-feed-skills-badge" hidden></span>
				<span class="rl-filter-btn__caret" aria-hidden="true">▾</span>
				<span class="rl-filter-btn__lock" aria-hidden="true">🔒</span>
			</button>
			<details class="rl-filter-sort-dd" id="rl-feed-sort-dd">
				<summary
					class="rl-filter-btn rl-filter-dropdown-btn<?php echo $rl_feed_tier === 'anon' ? ' rl-filter-btn--locked' : ''; ?>"
					id="rl-feed-sort-trigger"
					<?php echo $rl_feed_tier === 'anon' ? ' data-filter-locked="sort"' : ''; ?>
				>
					<span class="rl-filter-btn__label" id="rl-feed-sort-trigger-label"><?php esc_html_e('Сортировка', 'rawlead-kadence-child'); ?></span>
					<span class="rl-filter-btn__badge rl-filter-btn__badge--spacer" aria-hidden="true" hidden></span>
					<span class="rl-filter-btn__caret" aria-hidden="true">▾</span>
					<span class="rl-filter-btn__lock" aria-hidden="true">🔒</span>
				</summary>
				<div class="rl-sort-panel" id="rl-feed-sort-panel" role="group" aria-label="<?php esc_attr_e('Сортировка', 'rawlead-kadence-child'); ?>"></div>
			</details>
			<button type="button" class="rl-filter-mobile-trigger" id="rl-feed-filters-open" aria-expanded="false" aria-controls="rl-feed-sheet">
				<span class="rl-filter-mobile-trigger__icon" aria-hidden="true">☰</span>
				<span class="rl-filter-mobile-trigger__label"><?php esc_html_e('Фильтр', 'rawlead-kadence-child'); ?></span>
			</button>
			<button type="button" class="rl-filter-reset rl-feed-reset" hidden><?php esc_html_e('Сбросить фильтр', 'rawlead-kadence-child'); ?></button>
		</div>
	</div>
	<div class="rl-filter-hint" id="rl-filter-hint" hidden>
		<?php esc_html_e('Войди чтобы настраивать подбор по навыкам →', 'rawlead-kadence-child'); ?>
		<a href="<?php echo $cabinet_login; ?>"><?php esc_html_e('Войти в кабинет', 'rawlead-kadence-child'); ?></a>
	</div>
</div>
