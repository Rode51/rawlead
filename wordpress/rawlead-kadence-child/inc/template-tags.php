<?php
/**
 * Template tags for RawLead landing.
 *
 * @package RawLead_Kadence_Child
 */

declare(strict_types=1);

if (!defined('ABSPATH')) {
    exit;
}

function rawlead_get_part(string $slug): void {
    $file = RAWLEAD_CHILD_DIR . '/template-parts/rawlead/' . $slug . '.php';
    if (is_readable($file)) {
        include $file;
    }
}
