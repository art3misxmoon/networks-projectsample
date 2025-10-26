$(document).ready(function() {
    loadBalances();
    loadBlockchain();
    loadPeers();
    loadStatus();
    
    // refreshes every 5 sec
    setInterval(loadBalances, 5000);
    setInterval(loadBlockchain, 5000);
    setInterval(loadPeers, 5000);
    setInterval(loadStatus, 5000);
    setInterval(loadTransactions, 1000);
    
    // Initialize Pokémon card selection
    $.ajax({
        url: '/api/pokemon',
        type: 'GET',
        success: function(pokemonList) {
            createPokemonCardSelection('capture-pokemon', pokemonList);
        }
    });
    
    // Capture form submission
    $('#capture-form').submit(function(e) {
        e.preventDefault();
        
        const trainer = $('#capture-trainer').val();
        const pokemon = $('#capture-pokemon').val();
        
        if (!trainer || !pokemon) {
            $('#capture-status').html('<p class="error">Please select both a trainer and a Pokémon.</p>');
            return;
        }
        
        $('#capture-status').html('<p>Mining in progress... Please wait.</p>');
        
        $.ajax({
            url: '/api/capture',
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({
                trainer: trainer,
                pokemon: pokemon
            }),
            success: function(response) {
                $('#capture-status').html(`<p class="success">${response.message}</p>`);
                loadTransactions();
                
                // reset form/selection UI + refresh
                $('#capture-form')[0].reset();
                $('.pokemon-card').removeClass('selected');
                $('#capture-pokemon').next('.pokemon-selection-wrapper').remove();
                $('#capture-pokemon').removeClass('pokemon-select-hidden');
                
                $.ajax({
                    url: '/api/pokemon',
                    type: 'GET',
                    success: function(pokemonList) {
                        createPokemonCardSelection('capture-pokemon', pokemonList);
                    }
                });
            },
            error: function(xhr) {
                const response = JSON.parse(xhr.responseText);
                $('#capture-status').html(`<p class="error">${response.message}</p>`);
            }
        });
    });
    
    // Trade form submission
    $('#trade-form').submit(function(e) {
        e.preventDefault();
        
        const trainer1 = $('#trade-trainer1').val();
        const pokemon1 = $('#trade-pokemon1').val();
        const trainer2 = $('#trade-trainer2').val();
        const pokemon2 = $('#trade-pokemon2').val();
        
        if (!trainer1 || !pokemon1 || !trainer2 || !pokemon2) {
            $('#trade-status').html('<p class="error">Please select all required fields.</p>');
            return;
        }
        
        $('#trade-status').html('<p>Mining in progress... Please wait.</p>');
        
        $.ajax({
            url: '/api/trade',
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({
                trainer1: trainer1,
                pokemon1: pokemon1,
                trainer2: trainer2,
                pokemon2: pokemon2
            }),
            success: function(response) {
                $('#trade-status').html(`<p class="success">${response.message}</p>`);
                loadTransactions()
                
                // reset form/selection UI + refresh
                $('#trade-form')[0].reset();

                $('.pokemon-card').removeClass('selected');

                $('#trade-pokemon1').next('.pokemon-selection-wrapper').remove();
                $('#trade-pokemon2').next('.pokemon-selection-wrapper').remove();
                $('#trade-pokemon1').removeClass('pokemon-select-hidden');
                $('#trade-pokemon2').removeClass('pokemon-select-hidden');
            },
            error: function(xhr) {
                const response = JSON.parse(xhr.responseText);
                $('#trade-status').html(`<p class="error">${response.message}</p>`);
            }
        });
    });
    
    // Update trade form
    $('#trade-trainer1').on('change', function() {
        updateTrainerPokemonCards('trade-trainer1', 'trade-pokemon1');
    });

    $('#trade-trainer2').on('change', function() {
        updateTrainerPokemonCards('trade-trainer2', 'trade-pokemon2');
    });
});

/**
 * Load the connection and network status onto the UI.
 */
function loadStatus() {
    $.ajax({
        url: '/api/status',
        type: 'GET',
        success: function(status) {
            let html = `<div class="status-info">
                <p>Peer ID: <strong>${status.peer_id}</strong></p>
                <p>Tracker: <strong>${status.tracker}</strong></p>
                <p>Blockchain Length: <strong>${status.blockchain_length} blocks</strong></p>
                <p>Connected Peers: <strong>${status.connected_peers}</strong></p>
                <p>Network Status: <strong class="${status.network_status === 'connected' ? 'connected' : 'disconnected'}">${status.network_status}</strong></p>
            </div>`;
            
            $('#status-container').html(html);
        },
        error: function() {
            $('#status-container').html('<p class="error">Failed to load status information.</p>');
        }
    });
}

/**
 * Load balances of each trainer onto the UI.
 */
function loadBalances() {
    $.ajax({
        url: '/api/balances',
        type: 'GET',
        success: function(balances) {
            if (Object.keys(balances).length === 0) {
                $('#balances-container').html('<p>No trainers registered yet.</p>');
                return;
            }

            // Pokémon list for sprites
            $.ajax({
                url: '/api/pokemon',
                type: 'GET',
                success: function(pokemonList) {
                    let html = '<div class="balances">';
                    
                    for (const trainer in balances) {
                        html += `<div class="trainer-balance">
                            <h3>${trainer}</h3>
                            <ul>`;
                        
                        balances[trainer].forEach(pokemon => {
                            // map pkmn name to index for sprite
                            const index = pokemonList.findIndex(p => p === pokemon);
                            if (index !== -1) {
                                const paddedIndex = (index + 1).toString().padStart(4, '0');
                                html += `<li>
                                    <img src="/static/sprites/${paddedIndex}.png" width="20" height="20" alt="${pokemon}">
                                    ${pokemon}
                                </li>`;
                            } else {
                                html += `<li>${pokemon}</li>`;
                            }
                        });
                        
                        html += `</ul>
                            </div>`;
                    }
                    
                    html += '</div>';
                    $('#balances-container').html(html);
                },
                error: function() {
                    // Fallback
                    let html = '<div class="balances">';
                    
                    for (const trainer in balances) {
                        html += `<div class="trainer-balance">
                            <h3>${trainer}</h3>
                            <ul>`;
                        
                        balances[trainer].forEach(pokemon => {
                            html += `<li>${pokemon}</li>`;
                        });
                        
                        html += `</ul>
                            </div>`;
                    }
                    
                    html += '</div>';
                    $('#balances-container').html(html);
                }
            });
        },
        error: function() {
            $('#balances-container').html('<p class="error">Failed to load balances.</p>');
        }
    });
}

/**
 * Load the transactions list onto the UI, based on the blockchain.
 */
function loadTransactions() {
    $.ajax({
        url: '/api/transactions',
        type: 'GET',
        success: function(transactions) {
            $(".transactions").empty();
            
            if (transactions.length === 0) {
                $(".transactions").html('<p>No pending transactions.</p>');
                return;
            }
            
            for (let i = 0; i < transactions.length; i++) {
                let transaction = transactions[i];

                if (transaction.length == 2) {
                    $(".transactions").append(`
                        <div class='block'>
                            <div class='block-content'>
                                ${transaction[0]} captured ${transaction[1]}
                            </div>
                        </div>
                    `);
                } else if (transaction.length == 4) {
                    $(".transactions").append(`
                        <div class='block'>
                            <div class='block-content'>
                                ${transaction[0]} traded ${transaction[1]} to ${transaction[2]} for ${transaction[3]}
                            </div>
                        </div>
                    `);
                }
            }
            
            // Only show the submit button if there are transactions
            if (transactions.length > 0) {
                $(".transactions").append(`
                    <button class="transaction-submit btn">Mine Block</button>
                `);
                
                // Attach click handler
                $(".transaction-submit").click(function() {
                    $.ajax({
                        url: '/api/execute',
                        type: 'GET',
                        success: function(result) {
                            if (result.status === 'success') {
                                loadTransactions();
                                loadBalances();
                                loadBlockchain();
                            } else {
                                alert(result.message);
                            }
                        }
                    });
                });
            }
        },
        error: function() {
            $('.transactions').html('<p class="error">Failed to load transactions.</p>');
        }
    });
}

/**
 * Load and display Blockchain
 */
function loadBlockchain() {
    $.ajax({
        url: '/api/blockchain',
        type: 'GET',
        success: function(blockchain) {
            if (blockchain.length === 0) {
                $('#blockchain-container').html('<p>No blocks in the chain yet.</p>');
                return;
            }
            
            let html = '<div class="blockchain">';
            
            blockchain.forEach((block, index) => {
                html += `<div class="block">
                    <div class="block-header">
                        <h3>Block #${block.blockID}</h3>
                        <div class="block-hash">
                            <span>Hash: ${block.currHash.substring(0, 15)}...</span>
                        </div>
                    </div>
                    <div class="block-content">`;
                
                if (block.captures.length > 0) {
                    html += `<div class="captures">
                        <h4>Captures:</h4>
                        <ul>`;
                    
                    block.captures.forEach(capture => {
                        html += `<li>${capture[0]} captured ${capture[1]}</li>`;
                    });
                    
                    html += `</ul>
                        </div>`;
                }
                
                if (block.trades.length > 0) {
                    html += `<div class="trades">
                        <h4>Trades:</h4>
                        <ul>`;
                    
                    block.trades.forEach(trade => {
                        html += `<li>${trade[0]} traded ${trade[1]} to ${trade[2]} for ${trade[3]}</li>`;
                    });
                    
                    html += `</ul>
                        </div>`;
                }
                
                html += `</div>
                    </div>`;
            });
            
            html += '</div>';
            $('#blockchain-container').html(html);
        },
        error: function() {
            $('#blockchain-container').html('<p class="error">Failed to load blockchain.</p>');
        }
    });
}

/**
 * Load and display Peers
 */
function loadPeers() {
    $.ajax({
        url: '/api/peers',
        type: 'GET',
        success: function(peers) {
            if (peers.length === 0) {
                $('#peers-container').html('<p>No other peers connected.</p>');
                return;
            }
            
            let html = '<div class="peers">';
            html += '<h3>Connected Peers:</h3>';
            html += '<ul>';
            
            peers.forEach(peer => {
                html += `<li>${peer}</li>`;
            });
            
            html += '</ul></div>';
            $('#peers-container').html(html);
        },
        error: function() {
            $('#peers-container').html('<p class="error">Failed to load peer information.</p>');
        }
    });
}
