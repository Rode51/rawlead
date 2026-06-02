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
	<div class="rl-filter-bar" id="rl-feed-sidebar" aria-label="<?php esc_attr_e('Фильтры', 'rawlead-kadence-child'); ?>">
		<div class="rl-filter-bar__inner" id="rl-feed-sidebar-scroll">
			<fieldset class="rl-feed-filter rl-feed-filter--source is-visually-hidden">
				<legend><?php esc_html_e('Источник', 'rawlead-kadence-child'); ?></legend>
				<label class="rl-feed-chip is-active"><input type="radio" name="source" value="" checked> <?php esc_html_e('Все', 'rawlead-kadence-child'); ?></label>
				<label class="rl-feed-chip"><input type="radio" name="source" value="fl"> FL.ru</label>
				<label class="rl-feed-chip"><input type="radio" name="source" value="kwork"> Kwork</label>
				<label class="rl-feed-chip"><input type="radio" name="source" value="youdo"> YouDo</label>
				<label class="rl-feed-chip"><input type="radio" name="source" value="freelance_ru"> Freelance.ru</label>
				<label class="rl-feed-chip"><input type="radio" name="source" value="freelancejob"> FreelanceJob</label>
				<label class="rl-feed-chip"><input type="radio" name="source" value="pchyol"> Пчёл.нет</label>
				<label class="rl-feed-chip"><input type="radio" name="source" value="tg"> Telegram</label>
			</fieldset>
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
			<div class="rl-filter-bar__actions">
				<button type="button" class="rl-filter-dropdown-btn rl-feed-skills-dd__trigger" id="rl-feed-skills-trigger">
					<span class="rl-feed-skills-dd__label" id="rl-feed-skills-trigger-label"><?php esc_html_e('Навыки', 'rawlead-kadence-child'); ?></span>
					<span class="rl-feed-skills-dd__badge" id="rl-feed-skills-badge" hidden></span>
				</button>
				<details class="rl-filter-sort-dd">
					<summary class="rl-filter-dropdown-btn" id="rl-feed-sort-trigger"><?php esc_html_e('Дата ▾', 'rawlead-kadence-child'); ?></summary>
					<div class="rl-sort-panel">
						<label class="rl-sort-option is-active"><input type="radio" name="sort" value="time" checked> <?php esc_html_e('Дата', 'rawlead-kadence-child'); ?></label>
						<label class="rl-sort-option"><input type="radio" name="sort" value="match"> <?php esc_html_e('По совместимости', 'rawlead-kadence-child'); ?></label>
					</div>
				</details>
				<button type="button" class="rl-filter-dropdown-btn rl-filter-mobile-trigger" id="rl-feed-filters-open" aria-expanded="false" aria-controls="rl-feed-sheet">
					<?php esc_html_e('Фильтр', 'rawlead-kadence-child'); ?>
				</button>
				<button type="button" class="rl-filter-reset rl-feed-reset" hidden><?php esc_html_e('Сбросить фильтр', 'rawlead-kadence-child'); ?></button>
			</div>
		</div>
	</div>
	<p class="rl-feed-delay-notice" id="rl-feed-delay-notice" hidden></p>
	<div class="rl-container rl-feed-main-wrap">
		<header class="rl-feed-head">
			<h1 class="rl-feed-head__title"><?php esc_html_e('Лента заказов', 'rawlead-kadence-child'); ?></h1>
			<p class="rl-feed-head__count" id="rl-feed-count" aria-live="polite"></p>
		</header>
		<div class="rl-feed-banner" id="rl-feed-error" role="alert" hidden></div>
		<div class="rl-feed-list" id="rl-feed-list" aria-live="polite"></div>
		<div class="rl-feed-pagination" id="rl-feed-pagination">
			<button type="button" class="rl-btn rl-btn--primary rl-btn--load-more" id="rl-feed-load-more">
				<?php esc_html_e('Ещё лиды', 'rawlead-kadence-child'); ?> <span class="rl-btn__arrow" aria-hidden="true">→</span>
			</button>
			<span class="rl-feed-pagination__count" id="rl-feed-pagination-count"><?php esc_html_e('Показано', 'rawlead-kadence-child'); ?> <span id="rl-feed-shown">0</span> <?php esc_html_e('из', 'rawlead-kadence-child'); ?> <span id="rl-feed-total">0</span></span>
			<div class="rl-feed-loading" id="rl-feed-loading" role="status" aria-live="polite" hidden>
				<span class="rl-feed-loading__spinner" aria-hidden="true"></span>
				<span class="rl-feed-loading__text"><?php esc_html_e('Подбираем...', 'rawlead-kadence-child'); ?></span>
			</div>
		</div>
		<p class="rl-feed-end" id="rl-feed-end" hidden><?php esc_html_e('Все заказы показаны', 'rawlead-kadence-child'); ?></p>
	</div>
	<div class="rl-feed-skills-modal" id="rl-feed-skills-modal" hidden>
		<div class="rl-feed-skills-modal__overlay" id="rl-feed-skills-modal-overlay" aria-hidden="true"></div>
		<div class="rl-feed-skills-modal__panel rl-skill-tree" role="dialog" aria-modal="true" aria-labelledby="rl-feed-skills-title">
			<div class="rl-skill-tree__handle" aria-hidden="true"></div>
			<header class="rl-skill-tree__header">
				<h3 class="rl-skill-tree__title" id="rl-feed-skills-title"><?php esc_html_e('Навыки', 'rawlead-kadence-child'); ?></h3>
				<p class="rl-skill-tree__counter" id="rl-feed-skill-tree-counter" aria-live="polite"><?php esc_html_e('Выбрано 0 / 12', 'rawlead-kadence-child'); ?></p>
				<button type="button" class="rl-skill-tree__close" id="rl-feed-skill-tree-close" aria-label="<?php esc_attr_e('Закрыть', 'rawlead-kadence-child'); ?>">✕</button>
			</header>
			<p class="rl-skill-tree__hint" id="rl-feed-skill-tree-hint" hidden><?php esc_html_e('Выберите навыки и нажмите Применить', 'rawlead-kadence-child'); ?></p>
			<p class="rl-skill-tree__limit-msg" id="rl-feed-skill-tree-limit" hidden><?php esc_html_e('Максимум 12 навыков — сними лишние, чтобы добавить новые', 'rawlead-kadence-child'); ?></p>
			<div class="rl-skill-tree__body" id="rl-feed-skill-tree-body">
				<div class="rl-skill-tree__roots" id="rl-feed-skill-tree-roots" aria-live="polite"></div>
				<button type="button" class="rl-feed-skills-rare" id="rl-feed-skills-rare" hidden><?php esc_html_e('Ещё навыки', 'rawlead-kadence-child'); ?></button>
			</div>
			<footer class="rl-skill-tree__footer">
				<button type="button" class="rl-btn rl-btn--primary rl-feed-skills-apply" id="rl-feed-skills-apply" title="<?php esc_attr_e('Порядок изменится. Заказы не исчезнут.', 'rawlead-kadence-child'); ?>"><?php esc_html_e('Применить', 'rawlead-kadence-child'); ?></button>
				<button type="button" class="rl-btn rl-btn--ghost rl-feed-skills-my" id="rl-feed-skills-my"><?php esc_html_e('Мои навыки', 'rawlead-kadence-child'); ?></button>
				<button type="button" class="rl-skill-tree__reset rl-feed-skills-clear" id="rl-feed-skills-clear"><?php esc_html_e('Сбросить', 'rawlead-kadence-child'); ?></button>
			</footer>
		</div>
	</div>
	<div class="rl-feed-sheet" id="rl-feed-sheet" hidden>
		<div class="rl-feed-sheet__overlay" id="rl-feed-sheet-overlay"></div>
		<div class="rl-feed-sheet__panel" role="dialog" aria-modal="true" aria-label="<?php esc_attr_e('Фильтры', 'rawlead-kadence-child'); ?>">
			<div class="rl-feed-sheet__head">
				<span class="rl-feed-sheet__title"><?php esc_html_e('Фильтры', 'rawlead-kadence-child'); ?></span>
				<button type="button" class="rl-feed-sheet__close" id="rl-feed-sheet-close" aria-label="<?php esc_attr_e('Закрыть фильтры', 'rawlead-kadence-child'); ?>">✕</button>
			</div>
			<div class="rl-feed-sheet__body" id="rl-feed-sheet-body"></div>
			<div class="rl-feed-sheet__actions">
				<button type="button" class="rl-btn rl-btn--primary" id="rl-feed-sheet-apply"><?php esc_html_e('Применить →', 'rawlead-kadence-child'); ?></button>
				<button type="button" class="rl-btn rl-btn--ghost" id="rl-feed-sheet-reset"><?php esc_html_e('Сбросить', 'rawlead-kadence-child'); ?></button>
			</div>
		</div>
	</div>
</main>
<?php
rawlead_get_part('footer');
get_footer();
