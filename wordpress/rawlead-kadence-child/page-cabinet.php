<?php
/**
 * Template: /cabinet — персональная лента (final_rank) + теги.
 *
 * @package RawLead_Kadence_Child
 */

declare(strict_types=1);

get_header();
rawlead_get_part('header');
?>
<?php
$rawlead_cabinet_is_local = rawlead_is_local_dev();
$rawlead_cabinet_login_url = rawlead_cabinet_login_url();
?>
<main id="primary" class="rl-app rl-app--cabinet rl-cabinet--gate site-main" data-rl-app="cabinet">
	<section class="rl-cabinet-login" id="rl-cabinet-login">
		<div class="rl-cabinet-login__card">
			<h1 class="rl-cabinet-login__title"><?php esc_html_e('Кабинет', 'rawlead-kadence-child'); ?></h1>
			<p class="rl-cabinet-login__lead"><?php esc_html_e('Войдите через Telegram — сохраним ваши теги и персональную ленту.', 'rawlead-kadence-child'); ?></p>
			<div id="rl-telegram-login-widget" class="rl-cabinet-login__widget"></div>
			<p class="rl-cabinet-login__state rl-cabinet-login__state--info" id="rl-cabinet-login-state" aria-live="polite"></p>
			<p class="rl-cabinet-login__hint" id="rl-cabinet-login-hint" hidden></p>
			<?php if ($rawlead_cabinet_is_local) : ?>
			<p class="rl-cabinet-login__hint">
				<?php esc_html_e('Если видите серый/битый блок вместо кнопки Telegram — браузер не открывает telegram.org. Откройте кабинет на 127.0.0.1 и включите VPN/прокси или отключите блокировщик для telegram.org.', 'rawlead-kadence-child'); ?>
			</p>
			<?php else : ?>
			<p class="rl-cabinet-login__hint">
				<?php esc_html_e('Если кнопка Telegram не загрузилась — используйте fallback ниже или отключите блокировщик для telegram.org.', 'rawlead-kadence-child'); ?>
			</p>
			<?php endif; ?>
			<div class="rl-cabinet-login__fallback" id="rl-cabinet-login-fallback" hidden>
				<p class="rl-cabinet-login__hint"><?php esc_html_e('Fallback вход без iframe: откройте авторизацию в новом окне и вернитесь обратно в /cabinet/.', 'rawlead-kadence-child'); ?></p>
				<p class="rl-cabinet-login__direct">
					<a class="rl-btn rl-btn--primary" id="rl-cabinet-fallback-link" href="#" target="_blank">
						<?php esc_html_e('Войти через Telegram (fallback)', 'rawlead-kadence-child'); ?>
					</a>
				</p>
			</div>
			<?php if ($rawlead_cabinet_is_local) : ?>
			<p class="rl-cabinet-login__direct">
				<a class="rl-btn rl-btn--ghost" href="<?php echo esc_url($rawlead_cabinet_login_url); ?>">
					<?php esc_html_e('Открыть по адресу для Telegram (127.0.0.1)', 'rawlead-kadence-child'); ?>
				</a>
			</p>
			<?php endif; ?>
		</div>
	</section>
	<div class="rl-container rl-app__layout rl-cabinet-app" id="rl-cabinet-app" hidden>
		<aside class="rl-feed-sidebar" id="rl-cabinet-sidebar" aria-label="<?php esc_attr_e('Фильтры', 'rawlead-kadence-child'); ?>">
			<h2 class="rl-feed-sidebar__title"><?php esc_html_e('Фильтры', 'rawlead-kadence-child'); ?></h2>
			<fieldset class="rl-feed-filter">
				<legend><?php esc_html_e('Источник', 'rawlead-kadence-child'); ?></legend>
				<label class="rl-feed-chip is-active"><input type="radio" name="source" value="" checked> <?php esc_html_e('Все', 'rawlead-kadence-child'); ?></label>
				<label class="rl-feed-chip"><input type="radio" name="source" value="fl"> FL.ru</label>
				<label class="rl-feed-chip"><input type="radio" name="source" value="kwork"> Kwork</label>
				<label class="rl-feed-chip"><input type="radio" name="source" value="tg"> Telegram</label>
			</fieldset>
			<fieldset class="rl-feed-filter rl-feed-filter--category">
				<legend><?php esc_html_e('Категория', 'rawlead-kadence-child'); ?></legend>
				<label class="rl-feed-chip is-active" id="filter-category-all">
					<input type="checkbox" name="category" value="" checked>
					<?php esc_html_e('Все', 'rawlead-kadence-child'); ?>
				</label>
				<label class="rl-feed-chip" id="filter-category-dev">
					<input type="checkbox" name="category" value="dev">
					<span class="rl-feed-chip__label rl-feed-chip__label--full"><?php esc_html_e('Разработка', 'rawlead-kadence-child'); ?></span>
					<span class="rl-feed-chip__label rl-feed-chip__label--short"><?php esc_html_e('Код', 'rawlead-kadence-child'); ?></span>
				</label>
				<label class="rl-feed-chip" id="filter-category-design">
					<input type="checkbox" name="category" value="design">
					<span class="rl-feed-chip__label rl-feed-chip__label--full"><?php esc_html_e('Дизайн', 'rawlead-kadence-child'); ?></span>
					<span class="rl-feed-chip__label rl-feed-chip__label--short"><?php esc_html_e('Дизайн', 'rawlead-kadence-child'); ?></span>
				</label>
				<label class="rl-feed-chip" id="filter-category-marketing">
					<input type="checkbox" name="category" value="marketing">
					<span class="rl-feed-chip__label rl-feed-chip__label--full"><?php esc_html_e('Маркетинг', 'rawlead-kadence-child'); ?></span>
					<span class="rl-feed-chip__label rl-feed-chip__label--short"><?php esc_html_e('SMM', 'rawlead-kadence-child'); ?></span>
				</label>
				<label class="rl-feed-chip" id="filter-category-text">
					<input type="checkbox" name="category" value="text">
					<span class="rl-feed-chip__label rl-feed-chip__label--full"><?php esc_html_e('Тексты', 'rawlead-kadence-child'); ?></span>
					<span class="rl-feed-chip__label rl-feed-chip__label--short"><?php esc_html_e('Тексты', 'rawlead-kadence-child'); ?></span>
				</label>
			</fieldset>
			<fieldset class="rl-feed-filter">
				<legend><?php esc_html_e('Совместимость', 'rawlead-kadence-child'); ?></legend>
				<label class="rl-feed-chip is-active"><input type="radio" name="min_score" value="0" checked> <?php esc_html_e('Любая', 'rawlead-kadence-child'); ?></label>
				<label class="rl-feed-chip"><input type="radio" name="min_score" value="50"> <?php esc_html_e('От 50%', 'rawlead-kadence-child'); ?></label>
				<label class="rl-feed-chip"><input type="radio" name="min_score" value="70"> <?php esc_html_e('От 70%', 'rawlead-kadence-child'); ?></label>
			</fieldset>
			<button type="button" class="rl-feed-reset rl-link-arrow" hidden><?php esc_html_e('Сбросить фильтры', 'rawlead-kadence-child'); ?></button>
		</aside>
		<div class="rl-feed-main">
			<header class="rl-cabinet-head">
				<h1 class="rl-cabinet-head__title"><?php esc_html_e('Мои заказы', 'rawlead-kadence-child'); ?></h1>
				<p class="rl-cabinet-head__label"><?php esc_html_e('Ваши теги:', 'rawlead-kadence-child'); ?></p>
				<div class="rl-cabinet-tags" id="rl-cabinet-tags" role="list" aria-live="polite"></div>
				<p class="rl-cabinet-head__hint rl-cabinet-head__hint--empty" id="rl-cabinet-tags-hint" hidden>
					<?php esc_html_e('Добавьте навыки — ИИ покажет подходящие заказы', 'rawlead-kadence-child'); ?>
				</p>
			</header>
			<header class="rl-feed-head rl-cabinet-feed-head">
				<p class="rl-feed-head__count" id="rl-cabinet-count" aria-live="polite"></p>
				<button type="button" class="rl-btn rl-btn--ghost rl-feed-filters-btn" id="rl-cabinet-filters-open" aria-expanded="false">
					<?php esc_html_e('Фильтры', 'rawlead-kadence-child'); ?>
				</button>
			</header>
			<div class="rl-feed-banner" id="rl-cabinet-error" role="alert" hidden></div>
			<div class="rl-cabinet-empty rl-cabinet-empty--no-tags" id="rl-cabinet-no-tags" hidden>
				<p><?php esc_html_e('Добавьте навыки — ИИ покажет подходящие заказы', 'rawlead-kadence-child'); ?></p>
				<button type="button" class="rl-btn rl-btn--primary" id="rl-cabinet-add-first"><?php esc_html_e('Добавить навык', 'rawlead-kadence-child'); ?></button>
			</div>
			<div class="rl-cabinet-empty rl-cabinet-empty--no-match" id="rl-cabinet-no-match" hidden>
				<p><?php esc_html_e('Пока нет заказов по вашим навыкам. Попробуйте расширить профиль.', 'rawlead-kadence-child'); ?></p>
				<button type="button" class="rl-btn rl-btn--ghost" id="rl-cabinet-change-skills"><?php esc_html_e('Изменить навыки', 'rawlead-kadence-child'); ?></button>
			</div>
			<div class="rl-feed-list" id="rl-cabinet-list" aria-live="polite"></div>
			<div class="rl-feed-sentinel" id="rl-cabinet-sentinel" aria-hidden="true"></div>
			<p class="rl-feed-end" id="rl-cabinet-end" hidden><?php esc_html_e('Все заказы показаны', 'rawlead-kadence-child'); ?></p>
		</div>
	</div>
	<div class="rl-feed-sheet" id="rl-cabinet-sheet" hidden>
		<div class="rl-feed-sheet__overlay" id="rl-cabinet-sheet-overlay"></div>
		<div class="rl-feed-sheet__panel" role="dialog" aria-modal="true" aria-label="<?php esc_attr_e('Фильтры', 'rawlead-kadence-child'); ?>">
			<div class="rl-feed-sheet__body" id="rl-cabinet-sheet-body"></div>
			<div class="rl-feed-sheet__actions">
				<button type="button" class="rl-btn rl-btn--primary" id="rl-cabinet-sheet-apply"><?php esc_html_e('Применить', 'rawlead-kadence-child'); ?></button>
				<button type="button" class="rl-btn rl-btn--ghost" id="rl-cabinet-sheet-reset"><?php esc_html_e('Сбросить', 'rawlead-kadence-child'); ?></button>
			</div>
		</div>
	</div>
</main>
<?php
rawlead_get_part('footer');
get_footer();
