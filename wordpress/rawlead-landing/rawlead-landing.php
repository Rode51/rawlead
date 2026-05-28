<?php
/**
 * Plugin Name: RawLead Landing
 * Description: Скелет страниц RawLead (Local): home, how, pricing, faq, contact + меню.
 * Version: 0.3.1
 * Author: RawLead
 * Text Domain: rawlead-landing
 */

declare(strict_types=1);

if (!defined('ABSPATH')) {
    exit;
}

final class RawLead_Landing {
    private const PAGES = [
        'home'    => 'Главная',
        'how'     => 'Как работает',
        'pricing' => 'Тарифы',
        'faq'     => 'Вопросы',
        'contact' => 'Контакты',
        'lenta'   => 'Лента',
        'cabinet' => 'Кабинет',
    ];

    public static function init(): void {
        register_activation_hook(__FILE__, [self::class, 'on_activate']);
        add_action('admin_notices', [self::class, 'admin_notice']);
    }

    public static function on_activate(): void {
        self::ensure_permalinks();
        $ids = self::ensure_pages();
        self::ensure_front_page($ids['home'] ?? 0);
        self::ensure_menu($ids);
        update_option('blogname', 'RawLead');
        update_option('blogdescription', 'Unfiltered freelance leads');
        flush_rewrite_rules();
    }

    private static function ensure_permalinks(): void {
        if (get_option('permalink_structure')) {
            return;
        }
        update_option('permalink_structure', '/%postname%/');
    }

    /** @return array<string, int> slug => post_id */
    private static function ensure_pages(): array {
        $ids = [];
        foreach (self::PAGES as $slug => $title) {
            $existing = get_page_by_path($slug, OBJECT, 'page');
            $content = self::load_content($slug);
            if ($existing instanceof WP_Post) {
                wp_update_post([
                    'ID'           => $existing->ID,
                    'post_title'   => $title,
                    'post_content' => $content,
                    'post_status'  => 'publish',
                ]);
                $ids[$slug] = (int) $existing->ID;
                continue;
            }
            $post_id = wp_insert_post([
                'post_title'   => $title,
                'post_name'    => $slug,
                'post_content' => $content,
                'post_status'  => 'publish',
                'post_type'    => 'page',
            ], true);
            if (!is_wp_error($post_id) && $post_id) {
                $ids[$slug] = (int) $post_id;
            }
        }
        return $ids;
    }

    private static function load_content(string $slug): string {
        $path = plugin_dir_path(__FILE__) . 'content/' . $slug . '.html';
        if (is_readable($path)) {
            return (string) file_get_contents($path);
        }
        return '<p>Конент: docs/ops/wp-skeleton/' . esc_html($slug) . '.md</p>';
    }

    private static function ensure_front_page(int $home_id): void {
        if ($home_id <= 0) {
            return;
        }
        update_option('show_on_front', 'page');
        update_option('page_on_front', $home_id);
    }

    /** @param array<string, int> $ids */
    private static function ensure_menu(array $ids): void {
        $menu_name = 'RawLead';
        $menu = wp_get_nav_menu_object($menu_name);
        $menu_id = $menu ? (int) $menu->term_id : (int) wp_create_nav_menu($menu_name);
        if ($menu_id <= 0) {
            return;
        }
        $items = wp_get_nav_menu_items($menu_id);
        $have = [];
        if (is_array($items)) {
            foreach ($items as $item) {
                if ($item->object === 'page') {
                    $have[(int) $item->object_id] = true;
                }
            }
        }
        $order = 0;
        foreach (self::PAGES as $slug => $title) {
            if (empty($ids[$slug]) || !empty($have[$ids[$slug]])) {
                continue;
            }
            wp_update_nav_menu_item($menu_id, 0, [
                'menu-item-title'     => $title,
                'menu-item-object'    => 'page',
                'menu-item-object-id' => $ids[$slug],
                'menu-item-type'      => 'post_type',
                'menu-item-status'    => 'publish',
                'menu-item-position'  => ++$order,
            ]);
        }
        $registered = get_registered_nav_menus();
        if ($registered === []) {
            return;
        }
        $locations = get_theme_mod('nav_menu_locations');
        if (!is_array($locations)) {
            $locations = [];
        }
        foreach (array_keys($registered) as $loc) {
            $locations[$loc] = $menu_id;
        }
        set_theme_mod('nav_menu_locations', $locations);
    }

    public static function admin_notice(): void {
        if (!current_user_can('edit_pages')) {
            return;
        }
        $screen = function_exists('get_current_screen') ? get_current_screen() : null;
        if ($screen && $screen->id !== 'dashboard') {
            return;
        }
        $missing = [];
        foreach (self::PAGES as $slug => $title) {
            if (!get_page_by_path($slug, OBJECT, 'page')) {
                $missing[] = sprintf('<code>%s</code>', esc_html($slug));
            }
        }
        if ($missing === []) {
            echo '<div class="notice notice-success"><p><strong>RawLead Landing:</strong> скелет (5 страниц) на месте.</p></div>';
            return;
        }
        echo '<div class="notice notice-warning"><p><strong>RawLead Landing:</strong> нет страниц: '
            . implode(', ', $missing)
            . '. Деактивируй и снова активируй плагин.</p></div>';
    }
}

RawLead_Landing::init();
