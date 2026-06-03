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
			<p class="rl-cabinet-login__lead"><?php esc_html_e('Настроишь навыки — лента покажет заказы под твой стек. Черновик отклика — за один клик.', 'rawlead-kadence-child'); ?></p>
			<button type="button" class="rl-btn rl-btn--primary rl-cabinet-login__btn" id="rl-cabinet-login-btn">
				<svg class="rl-cabinet-login__icon" width="20" height="20" viewBox="0 0 24 24" aria-hidden="true" focusable="false">
					<path fill="currentColor" d="M9.04 15.314l-.376 5.302c.538 0 .77-.231 1.049-.508l2.518-2.418 5.217 3.823c.957.527 1.637.251 1.898-.885l3.438-16.08.001-.001c.305-1.423-.514-1.98-1.447-1.634L1.12 9.775c-1.392.541-1.369 1.317-.236 1.667l4.913 1.533L18.9 5.48c.595-.394 1.136-.176.691.218"/>
				</svg>
				<?php esc_html_e('Войти через Telegram', 'rawlead-kadence-child'); ?>
			</button>
			<div class="rl-cabinet-login__qr" id="rl-cabinet-login-qr" hidden>
				<p class="rl-cabinet-login__qr-lead rl-cabinet-login__qr-lead--desktop"><?php esc_html_e('Отсканируйте камерой телефона — откроется бот, нажмите Start.', 'rawlead-kadence-child'); ?></p>
				<p class="rl-cabinet-login__qr-lead rl-cabinet-login__qr-lead--mobile"><?php esc_html_e('Откройте Telegram и нажмите Start. Эта страница останется открытой — кабинет войдёт сам.', 'rawlead-kadence-child'); ?></p>
				<img class="rl-cabinet-login__qr-img" id="rl-cabinet-login-qr-img" width="260" height="260" alt="<?php esc_attr_e('QR-код для входа через Telegram', 'rawlead-kadence-child'); ?>">
				<p class="rl-cabinet-login__qr-wait" id="rl-cabinet-login-qr-wait"><?php esc_html_e('Ждём подтверждение в Telegram…', 'rawlead-kadence-child'); ?></p>
				<p class="rl-cabinet-login__qr-link">
					<a class="rl-btn rl-btn--ghost" id="rl-cabinet-login-qr-link" href="#" target="_blank" rel="noopener"><?php esc_html_e('Открыть Telegram', 'rawlead-kadence-child'); ?></a>
				</p>
				<button type="button" class="rl-btn rl-btn--ghost rl-cabinet-login__qr-cancel" id="rl-cabinet-login-qr-cancel"><?php esc_html_e('Отмена', 'rawlead-kadence-child'); ?></button>
			</div>
			<p class="rl-cabinet-login__state" id="rl-cabinet-login-state" aria-live="polite" hidden></p>
			<p class="rl-cabinet-login__alt">
				<a class="rl-link-arrow" href="<?php echo esc_url('https://t.me/' . rawlead_tg_login_bot_username() . '?start=login'); ?>" target="_blank" rel="noopener">
					<?php esc_html_e('Или войти через @rawlead_bot →', 'rawlead-kadence-child'); ?>
				</a>
			</p>
			<?php if ($rawlead_cabinet_is_local) : ?>
			<p class="rl-cabinet-login__dev">
				<a class="rl-link-arrow" href="<?php echo esc_url($rawlead_cabinet_login_url); ?>">
					<?php esc_html_e('Локальный вход (127.0.0.1)', 'rawlead-kadence-child'); ?>
				</a>
			</p>
			<?php endif; ?>
		</div>
	</section>
	<div class="rl-container rl-app__layout rl-cabinet-app" id="rl-cabinet-app" hidden>
		<div class="rl-cabinet-user" id="rl-cabinet-user" hidden>
			<img class="rl-cabinet-user__avatar" id="rl-cabinet-user-avatar" alt="" width="40" height="40" hidden>
			<div class="rl-cabinet-user__info">
				<p class="rl-cabinet-user__label">
					<?php esc_html_e('В системе:', 'rawlead-kadence-child'); ?>
					<strong id="rl-cabinet-user-name"></strong>
				</p>
				<p class="rl-cabinet-user__hint">
					<a href="https://t.me/rawlead_bot" target="_blank" rel="noopener"><?php esc_html_e('Открыть @rawlead_bot', 'rawlead-kadence-child'); ?></a>
					<?php esc_html_e('· /start — push match-лидов', 'rawlead-kadence-child'); ?>
				</p>
			</div>
			<button type="button" class="rl-btn rl-btn--ghost" id="rl-cabinet-logout"><?php esc_html_e('Выйти', 'rawlead-kadence-child'); ?></button>
		</div>
		<section class="rl-cabinet-sub" id="rl-cabinet-sub" aria-labelledby="rl-cabinet-sub-title" hidden>
			<div class="rl-cabinet-sub__head">
				<h2 class="rl-cabinet-sub__title" id="rl-cabinet-sub-title"><?php esc_html_e('RawLead Premium', 'rawlead-kadence-child'); ?></h2>
				<span class="rl-cabinet-sub__badge" id="rl-cabinet-sub-badge" aria-live="polite"></span>
			</div>
			<p class="rl-cabinet-sub__price" id="rl-cabinet-sub-price"><?php esc_html_e('790 ₽/мес · или 300 ⭐ Stars', 'rawlead-kadence-child'); ?></p>
			<p class="rl-cabinet-sub__detail" id="rl-cabinet-sub-detail"></p>
			<div class="rl-cabinet-sub__actions">
				<a class="rl-btn rl-btn--primary rl-cabinet-sub__trial" id="rl-cabinet-sub-trial" href="<?php echo esc_url('https://t.me/' . rawlead_tg_login_bot_username() . '?start=trial'); ?>" target="_blank" rel="noopener" hidden>
					<?php esc_html_e('Попробовать 3 дня бесплатно', 'rawlead-kadence-child'); ?>
				</a>
				<a class="rl-btn rl-btn--ghost rl-cabinet-sub__pay" id="rl-cabinet-sub-pay" href="<?php echo esc_url('https://t.me/' . rawlead_tg_login_bot_username() . '?start=pay'); ?>" target="_blank" rel="noopener">
					<?php esc_html_e('Подключить Premium →', 'rawlead-kadence-child'); ?>
				</a>
				<button type="button" class="rl-btn rl-btn--ghost rl-cabinet-sub__pause" id="rl-cabinet-sub-pause" hidden disabled>
					<?php esc_html_e('Пауза', 'rawlead-kadence-child'); ?>
				</button>
				<button type="button" class="rl-btn rl-btn--ghost rl-cabinet-sub__resume" id="rl-cabinet-sub-resume" hidden>
					<?php esc_html_e('Возобновить', 'rawlead-kadence-child'); ?>
				</button>
				<a class="rl-btn rl-btn--ghost rl-cabinet-sub__billing" id="rl-cabinet-sub-billing" href="<?php echo esc_url('https://t.me/' . rawlead_tg_login_bot_username() . '?start=pay'); ?>" target="_blank" rel="noopener" hidden>
					<?php esc_html_e('Оплата', 'rawlead-kadence-child'); ?>
				</a>
			</div>
			<p class="rl-cabinet-sub__note" id="rl-cabinet-sub-note" hidden></p>
		</section>
		<section class="rl-cabinet-notif" id="rl-cabinet-notif" aria-labelledby="rl-cabinet-notif-title" hidden>
			<h2 class="rl-cabinet-notif__title" id="rl-cabinet-notif-title"><?php esc_html_e('Уведомления', 'rawlead-kadence-child'); ?></h2>
			<div class="rl-cabinet-notif__row">
				<span class="rl-cabinet-notif__label" id="rl-cabinet-notif-threshold-label"><?php esc_html_e('Уведомлять от % совпадения', 'rawlead-kadence-child'); ?></span>
				<div class="rl-cabinet-notif__chips" id="rl-cabinet-notif-threshold" role="group" aria-labelledby="rl-cabinet-notif-threshold-label">
					<?php
					foreach ( [ 30, 40, 50, 60, 70, 80, 90, 100 ] as $pct ) :
						$active = 60 === $pct ? ' is-active' : '';
						?>
					<button type="button" class="rl-notif-threshold-chip<?php echo esc_attr( $active ); ?>" data-value="<?php echo (int) $pct; ?>" aria-pressed="<?php echo 60 === $pct ? 'true' : 'false'; ?>"><?php echo (int) $pct; ?>%</button>
					<?php endforeach; ?>
				</div>
			</div>
			<div class="rl-cabinet-notif__row rl-cabinet-notif__row--toggle">
				<div class="rl-cabinet-notif__toggle-wrap">
					<span class="rl-cabinet-notif__label" id="rl-cabinet-notif-enabled-label"><?php esc_html_e('Push в Telegram', 'rawlead-kadence-child'); ?></span>
					<p class="rl-cabinet-notif__toggle-hint"><?php esc_html_e('Premium в @rawlead_bot — /pay или кнопка в кабинете. Нажми /start в боте.', 'rawlead-kadence-child'); ?></p>
				</div>
				<button type="button" class="rl-toggle" id="rl-cabinet-notif-enabled" role="switch" aria-checked="true" aria-labelledby="rl-cabinet-notif-enabled-label">
					<span class="rl-toggle__knob"></span>
				</button>
			</div>
			<p class="rl-cabinet-notif__status" id="rl-cabinet-notif-status" aria-live="polite"></p>
		</section>
		<p class="rl-cabinet-notif__hint" id="rl-cabinet-notif-hint" hidden>
			<?php esc_html_e('Push: активируй Premium (@rawlead_bot /pay) и /start — иначе уведомления не дойдут.', 'rawlead-kadence-child'); ?>
		</p>
		<div class="rl-feed-main rl-cabinet-inbox">
			<header class="rl-cabinet-head">
				<h1 class="rl-cabinet-head__title"><?php esc_html_e('Мои отклики', 'rawlead-kadence-child'); ?></h1>
				<p class="rl-cabinet-head__lead"><?php esc_html_e('Отклики с ленты — здесь. Новые заказы →', 'rawlead-kadence-child'); ?> <a href="<?php echo esc_url(rawlead_page_url('lenta')); ?>"><?php esc_html_e('Лента', 'rawlead-kadence-child'); ?></a></p>
				<p class="rl-cabinet-head__label"><?php esc_html_e('Твои навыки', 'rawlead-kadence-child'); ?></p>
				<div class="rl-cabinet-tags" id="rl-cabinet-tags" role="list" aria-live="polite"></div>
				<button type="button" class="rl-btn rl-btn--ghost rl-cabinet-tags-clear" id="rl-cabinet-tags-clear" hidden><?php esc_html_e('Сбросить', 'rawlead-kadence-child'); ?></button>
				<p class="rl-cabinet-head__hint rl-cabinet-head__hint--empty" id="rl-cabinet-tags-hint" hidden>
					<?php esc_html_e('Добавь навыки для совместимости →', 'rawlead-kadence-child'); ?>
				</p>
			</header>
			<header class="rl-feed-head rl-cabinet-feed-head">
				<p class="rl-feed-head__count" id="rl-cabinet-count" aria-live="polite"></p>
			</header>
			<div class="rl-feed-banner" id="rl-cabinet-error" role="alert" hidden></div>
			<div class="rl-cabinet-empty rl-cabinet-empty--no-tags" id="rl-cabinet-no-tags" hidden>
				<p><?php esc_html_e('Добавь навыки — покажем заказы под твой стек.', 'rawlead-kadence-child'); ?></p>
				<button type="button" class="rl-btn rl-btn--primary" id="rl-cabinet-add-first"><?php esc_html_e('Добавить навыки', 'rawlead-kadence-child'); ?></button>
			</div>
			<div class="rl-cabinet-empty rl-cabinet-empty--no-match" id="rl-cabinet-no-match" hidden>
				<p><?php esc_html_e('Откликнулся на ленте — черновик появится здесь.', 'rawlead-kadence-child'); ?></p>
				<a class="rl-btn rl-btn--primary" href="<?php echo esc_url(rawlead_page_url('lenta')); ?>"><?php esc_html_e('На ленту →', 'rawlead-kadence-child'); ?></a>
			</div>
			<div class="rl-cabinet-empty rl-cabinet-empty--no-match-free" id="rl-cabinet-no-match-free" hidden>
				<p><?php esc_html_e('Черновики откликов — с подпиской ИИ-агент.', 'rawlead-kadence-child'); ?></p>
				<a class="rl-btn rl-btn--primary" href="<?php echo esc_url(rawlead_page_url('pricing')); ?>"><?php esc_html_e('Тарифы →', 'rawlead-kadence-child'); ?></a>
			</div>
			<div class="rl-feed-list rl-inbox-list" id="rl-cabinet-list" aria-live="polite"></div>
			<div class="rl-feed-pagination" id="rl-cabinet-pagination">
				<button type="button" class="rl-btn rl-btn--primary rl-btn--load-more" id="rl-cabinet-load-more">
					<?php esc_html_e('Показать ещё', 'rawlead-kadence-child'); ?> <span class="rl-btn__arrow" aria-hidden="true">→</span>
				</button>
				<span class="rl-feed-pagination__count" id="rl-cabinet-pagination-count"><?php esc_html_e('Показано', 'rawlead-kadence-child'); ?> <span id="rl-cabinet-shown">0</span> <?php esc_html_e('из', 'rawlead-kadence-child'); ?> <span id="rl-cabinet-total">0</span></span>
				<div class="rl-feed-loading" id="rl-cabinet-loading" hidden>
					<span class="rl-feed-loading__spinner" aria-hidden="true"></span>
					<span><?php esc_html_e('Подбираем...', 'rawlead-kadence-child'); ?></span>
				</div>
			</div>
			<p class="rl-feed-end" id="rl-cabinet-end" hidden><?php esc_html_e('Все отклики показаны', 'rawlead-kadence-child'); ?></p>
		</div>
	</div>
	<div class="rl-cabinet-skills-modal" id="rl-cabinet-skills-modal" hidden>
		<div class="rl-cabinet-skills-modal__overlay" id="rl-cabinet-skills-modal-overlay" aria-hidden="true"></div>
		<div class="rl-cabinet-skills-modal__panel rl-skill-tree" role="dialog" aria-modal="true" aria-labelledby="rl-cabinet-skills-title">
			<div class="rl-skill-tree__handle" aria-hidden="true"></div>
			<header class="rl-skill-tree__header">
				<h3 class="rl-skill-tree__title" id="rl-cabinet-skills-title"><?php esc_html_e('Навыки', 'rawlead-kadence-child'); ?></h3>
				<p class="rl-skill-tree__counter" id="rl-cabinet-skill-tree-counter" aria-live="polite"><?php esc_html_e('Выбрано 0 / 12', 'rawlead-kadence-child'); ?></p>
				<button type="button" class="rl-skill-tree__close" id="rl-cabinet-skill-tree-close" aria-label="<?php esc_attr_e('Закрыть', 'rawlead-kadence-child'); ?>">✕</button>
			</header>
			<p class="rl-skill-tree__hint" id="rl-cabinet-skill-tree-hint" hidden><?php esc_html_e('Слишком широко — match упадёт. Оставь 6–8 ключевых.', 'rawlead-kadence-child'); ?></p>
			<p class="rl-skill-tree__limit-msg" id="rl-cabinet-skill-tree-limit" hidden><?php esc_html_e('Максимум 12 — сними лишние.', 'rawlead-kadence-child'); ?></p>
			<div class="rl-skill-tree__body" id="rl-cabinet-skill-tree-body">
				<div class="rl-skill-tree__roots" id="rl-cabinet-skill-tree-roots" aria-live="polite"></div>
			</div>
			<footer class="rl-skill-tree__footer">
				<button type="button" class="rl-btn rl-skill-tree__save" id="rl-cabinet-skills-apply" disabled><?php esc_html_e('Сохранить навыки →', 'rawlead-kadence-child'); ?></button>
				<p class="rl-skill-tree__save-error" id="rl-cabinet-skill-tree-save-error" role="alert" hidden><?php esc_html_e('Ошибка — попробуй снова', 'rawlead-kadence-child'); ?></p>
				<button type="button" class="rl-skill-tree__reset" id="rl-cabinet-skill-tree-reset"><?php esc_html_e('Сбросить всё', 'rawlead-kadence-child'); ?></button>
			</footer>
		</div>
	</div>
</main>
<?php
rawlead_get_part('footer');
get_footer();
