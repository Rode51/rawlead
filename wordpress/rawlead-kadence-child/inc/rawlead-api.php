<?php

/**

 * RawLead API — единый URL бэкенда + REST-прокси для WP (same-origin).

 *

 * Переопределение: define('RAWLEAD_API_URL', 'http://127.0.0.1:18766'); в wp-config.php

 *

 * @package RawLead_Kadence_Child

 */



declare(strict_types=1);



if (!defined('ABSPATH')) {

    exit;

}



/** MVP owner user (#1) — см. pg_storage._OWNER_USER_ID */

const RAWLEAD_OWNER_USER_ID = '00000000-0000-0000-0000-000000000001';



/** Базовый URL FastAPI (без завершающего слэша). */

function rawlead_api_base_url(): string {

    if (defined('RAWLEAD_API_URL')) {

        return rtrim((string) RAWLEAD_API_URL, '/');

    }

    return 'http://127.0.0.1:18766';

}



/** @return array<string, string> */

function rawlead_api_owner_headers(): array {

    return [

        'Accept'              => 'application/json',

        'X-RawLead-User-Id'   => RAWLEAD_OWNER_USER_ID,

    ];

}



/** @username бота для Telegram Login Widget (wp-config: RAWLEAD_TG_BOT_USERNAME). */

function rawlead_tg_login_bot_username(): string {

    if (defined('RAWLEAD_TG_BOT_USERNAME')) {

        $value = trim((string) RAWLEAD_TG_BOT_USERNAME);
        $normalized = ltrim(strtolower($value), '@');
        if ($normalized === 'rawlead_bot') {
            return 'rawlead_bot';
        }

    }

    return 'rawlead_bot';

}



/** Bearer из REST-запроса браузера. */

function rawlead_api_bearer_from_request(WP_REST_Request $request): string {

    $auth = $request->get_header('authorization');

    if (!is_string($auth) || $auth === '') {

        return '';

    }

    if (stripos($auth, 'Bearer ') !== 0) {

        return '';

    }

    return trim(substr($auth, 7));

}



/**

 * @return array<string, string>

 */

function rawlead_api_user_headers(WP_REST_Request $request, bool $owner_fallback = false): array {

    $headers = ['Accept' => 'application/json'];

    $bearer = rawlead_api_bearer_from_request($request);

    if ($bearer !== '') {

        $headers['Authorization'] = 'Bearer ' . $bearer;

        return $headers;

    }

    if ($owner_fallback) {

        return rawlead_api_owner_headers();

    }

    return $headers;

}



/**

 * @param array<string, scalar> $query

 * @return array<string, mixed>|WP_Error

 */

function rawlead_api_get(string $path, array $query = [], bool $owner = false): array|WP_Error {

    $url = rawlead_api_base_url() . $path;

    if ($query !== []) {

        $url .= '?' . http_build_query($query);

    }



    $headers = ['Accept' => 'application/json'];

    if ($owner) {

        $headers = rawlead_api_owner_headers();

    }



    $response = wp_remote_get($url, [

        'timeout' => 20,

        'headers' => $headers,

    ]);



    if (is_wp_error($response)) {

        return $response;

    }



    $code = (int) wp_remote_retrieve_response_code($response);

    $body = wp_remote_retrieve_body($response);

    $data = json_decode($body, true);



    if ($code < 200 || $code >= 300) {

        $detail = is_array($data) && isset($data['detail']) ? (string) $data['detail'] : $body;

        return new WP_Error('rawlead_api_http', $detail ?: 'API error', ['status' => $code]);

    }



    return is_array($data) ? $data : [];

}



/**

 * @param array<string, mixed> $body

 * @return array<string, mixed>|WP_Error

 */

function rawlead_api_put(string $path, array $body, bool $owner = false): array|WP_Error {

    $url = rawlead_api_base_url() . $path;

    $headers = [

        'Accept'       => 'application/json',

        'Content-Type' => 'application/json',

    ];

    if ($owner) {

        $headers = array_merge($headers, rawlead_api_owner_headers());

    }



    $response = wp_remote_request($url, [

        'method'  => 'PUT',

        'timeout' => 20,

        'headers' => $headers,

        'body'    => wp_json_encode($body),

    ]);



    if (is_wp_error($response)) {

        return $response;

    }



    $code = (int) wp_remote_retrieve_response_code($response);

    $raw = wp_remote_retrieve_body($response);

    $data = json_decode($raw, true);



    if ($code < 200 || $code >= 300) {

        $detail = is_array($data) && isset($data['detail']) ? (string) $data['detail'] : $raw;

        return new WP_Error('rawlead_api_http', $detail ?: 'API error', ['status' => $code]);

    }



    return is_array($data) ? $data : [];

}



/**

 * @param array<string, mixed> $body

 * @return array<string, mixed>|WP_Error

 */

function rawlead_api_post(string $path, array $body, array $extra_headers = []): array|WP_Error {

    $url = rawlead_api_base_url() . $path;

    $headers = array_merge(

        [

            'Accept'       => 'application/json',

            'Content-Type' => 'application/json',

        ],

        $extra_headers

    );



    $response = wp_remote_post($url, [

        'timeout' => 20,

        'headers' => $headers,

        'body'    => wp_json_encode($body),

    ]);



    if (is_wp_error($response)) {

        return $response;

    }



    $code = (int) wp_remote_retrieve_response_code($response);

    $raw = wp_remote_retrieve_body($response);

    $data = json_decode($raw, true);



    if ($code < 200 || $code >= 300) {

        $detail = is_array($data) && isset($data['detail']) ? (string) $data['detail'] : $raw;

        return new WP_Error('rawlead_api_http', $detail ?: 'API error', ['status' => $code]);

    }



    return is_array($data) ? $data : [];

}



add_action('rest_api_init', static function (): void {

    register_rest_route('rawlead/v1', '/auth/telegram', [

        'methods'             => 'POST',

        'permission_callback' => '__return_true',

        'callback'            => static function (WP_REST_Request $request): WP_REST_Response|WP_Error {

            $body = $request->get_json_params();

            if (!is_array($body)) {

                return new WP_Error('rawlead_invalid', 'Expected JSON body', ['status' => 400]);

            }

            $data = rawlead_api_post('/v1/auth/telegram', $body);

            if (is_wp_error($data)) {

                return $data;

            }

            return new WP_REST_Response($data, 200);

        },

    ]);




    register_rest_route('rawlead/v1', '/feed', [

        'methods'             => 'GET',

        'permission_callback' => '__return_true',

        'args'                => [

            'limit'     => ['type' => 'integer', 'default' => 20, 'minimum' => 1, 'maximum' => 100],

            'offset'    => ['type' => 'integer', 'default' => 0, 'minimum' => 0],

            'min_score' => ['type' => 'integer', 'default' => 0, 'minimum' => 0, 'maximum' => 100],

            'skills'    => ['type' => 'string', 'default' => ''],

            'category'  => ['type' => 'string', 'default' => ''],

            'sort'      => ['type' => 'string', 'default' => 'time'],

        ],

        'callback'            => static function (WP_REST_Request $request): WP_REST_Response|WP_Error {

            $query = [

                'limit'     => (int) $request->get_param('limit'),

                'offset'    => (int) $request->get_param('offset'),

                'min_score' => (int) $request->get_param('min_score'),

                'sort'      => (string) $request->get_param('sort'),

            ];

            $skills = trim((string) $request->get_param('skills'));

            if ($skills !== '') {

                $query['skills'] = $skills;

            }

            $category = trim((string) $request->get_param('category'));

            if ($category !== '') {

                $query['category'] = $category;

            }

            $data = rawlead_api_get('/v1/feed', $query);

            if (is_wp_error($data)) {

                return $data;

            }

            return new WP_REST_Response($data, 200);

        },

    ]);



    register_rest_route('rawlead/v1', '/leads/(?P<id>\d+)', [

        'methods'             => 'GET',

        'permission_callback' => '__return_true',

        'args'                => [

            'id' => ['type' => 'integer', 'required' => true],

        ],

        'callback'            => static function (WP_REST_Request $request): WP_REST_Response|WP_Error {

            $id = (int) $request->get_param('id');

            $data = rawlead_api_get('/v1/leads/' . $id);

            if (is_wp_error($data)) {

                return $data;

            }

            return new WP_REST_Response($data, 200);

        },

    ]);



    register_rest_route('rawlead/v1', '/skills/catalog', [

        'methods'             => 'GET',

        'permission_callback' => '__return_true',

        'callback'            => static function (WP_REST_Request $request): WP_REST_Response|WP_Error {

            $query = [];

            $category = trim((string) $request->get_param('category'));

            if ($category !== '') {

                $query['category'] = $category;

            }

            $data = rawlead_api_get('/v1/skills/catalog', $query);

            if (is_wp_error($data)) {

                return $data;

            }

            return new WP_REST_Response($data, 200);

        },

    ]);



    register_rest_route('rawlead/v1', '/me/feed', [

        'methods'             => 'GET',

        'permission_callback' => '__return_true',

        'args'                => [

            'limit'     => ['type' => 'integer', 'default' => 20, 'minimum' => 1, 'maximum' => 100],

            'offset'    => ['type' => 'integer', 'default' => 0, 'minimum' => 0],

            'min_score' => ['type' => 'integer', 'default' => 0, 'minimum' => 0, 'maximum' => 100],

            'skills'    => ['type' => 'string', 'default' => ''],

            'sort'      => ['type' => 'string', 'default' => 'match'],

        ],

        'callback'            => static function (WP_REST_Request $request): WP_REST_Response|WP_Error {

            $query = [

                'limit'     => (int) $request->get_param('limit'),

                'offset'    => (int) $request->get_param('offset'),

                'min_score' => (int) $request->get_param('min_score'),

                'sort'      => (string) $request->get_param('sort'),

            ];

            $skills = trim((string) $request->get_param('skills'));

            if ($skills !== '') {

                $query['skills'] = $skills;

            }

            $category = trim((string) $request->get_param('category'));

            if ($category !== '') {

                $query['category'] = $category;

            }

            $url = rawlead_api_base_url() . '/v1/me/feed';

            if ($query !== []) {

                $url .= '?' . http_build_query($query);

            }

            $response = wp_remote_get($url, [

                'timeout' => 20,

                'headers' => rawlead_api_user_headers($request, true),

            ]);

            if (is_wp_error($response)) {

                return $response;

            }

            $code = (int) wp_remote_retrieve_response_code($response);

            $raw = wp_remote_retrieve_body($response);

            $data = json_decode($raw, true);

            if ($code < 200 || $code >= 300) {

                $detail = is_array($data) && isset($data['detail']) ? (string) $data['detail'] : $raw;

                return new WP_Error('rawlead_api_http', $detail ?: 'API error', ['status' => $code]);

            }

            $data = is_array($data) ? $data : [];

            if (is_wp_error($data)) {

                return $data;

            }

            return new WP_REST_Response($data, 200);

        },

    ]);



    register_rest_route('rawlead/v1', '/me/tags', [

        [

            'methods'             => 'GET',

            'permission_callback' => '__return_true',

            'callback'            => static function (WP_REST_Request $request): WP_REST_Response|WP_Error {

                $url = rawlead_api_base_url() . '/v1/me/tags';

                $response = wp_remote_get($url, [

                    'timeout' => 20,

                    'headers' => rawlead_api_user_headers($request, true),

                ]);

                if (is_wp_error($response)) {

                    return $response;

                }

                $code = (int) wp_remote_retrieve_response_code($response);

                $raw = wp_remote_retrieve_body($response);

                $data = json_decode($raw, true);

                if ($code < 200 || $code >= 300) {

                    $detail = is_array($data) && isset($data['detail']) ? (string) $data['detail'] : $raw;

                    return new WP_Error('rawlead_api_http', $detail ?: 'API error', ['status' => $code]);

                }

                return new WP_REST_Response(is_array($data) ? $data : [], 200);

            },

        ],

        [

            'methods'             => 'PUT',

            'permission_callback' => '__return_true',

            'callback'            => static function (WP_REST_Request $request): WP_REST_Response|WP_Error {

                $tags = $request->get_json_params();

                if (!is_array($tags) || !isset($tags['tags']) || !is_array($tags['tags'])) {

                    return new WP_Error('rawlead_invalid', 'Expected {"tags":[]}', ['status' => 400]);

                }

                $url = rawlead_api_base_url() . '/v1/me/tags';

                $response = wp_remote_request($url, [

                    'method'  => 'PUT',

                    'timeout' => 20,

                    'headers' => array_merge(

                        rawlead_api_user_headers($request, true),

                        ['Content-Type' => 'application/json']

                    ),

                    'body'    => wp_json_encode(['tags' => $tags['tags']]),

                ]);

                if (is_wp_error($response)) {

                    return $response;

                }

                $code = (int) wp_remote_retrieve_response_code($response);

                $raw = wp_remote_retrieve_body($response);

                $data = json_decode($raw, true);

                if ($code < 200 || $code >= 300) {

                    $detail = is_array($data) && isset($data['detail']) ? (string) $data['detail'] : $raw;

                    return new WP_Error('rawlead_api_http', $detail ?: 'API error', ['status' => $code]);

                }

                return new WP_REST_Response(is_array($data) ? $data : [], 200);

            },

        ],

    ]);

});

