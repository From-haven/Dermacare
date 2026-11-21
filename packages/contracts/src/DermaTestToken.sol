// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

/**
 * @title DermaTestToken
 * @notice ERC20 test token for DermaCare Partner package test settlements on Avalanche Fuji.
 */
contract DermaTestToken {
    string public name = "DermaCare Test Token";
    string public symbol = "DTEST";
    uint8 public decimals = 18;
    uint256 public totalSupply;

    mapping(address => uint256) public balanceOf;
    mapping(address => mapping(address => uint256)) public allowance;
    mapping(address => uint256) public nonces;
    mapping(address => uint256) public lastFaucetAt;

    uint256 public constant FAUCET_AMOUNT = 1000 * 10**18;
    uint256 public constant FAUCET_COOLDOWN = 1 days;

    event Transfer(address indexed from, address indexed to, uint256 value);
    event Approval(address indexed owner, address indexed spender, uint256 value);

    function transfer(address to, uint256 value) external returns (bool) {
        require(balanceOf[msg.sender] >= value, "Insufficient balance");
        balanceOf[msg.sender] -= value;
        balanceOf[to] += value;
        emit Transfer(msg.sender, to, value);
        return true;
    }

    function approve(address spender, uint256 value) external returns (bool) {
        allowance[msg.sender][spender] = value;
        emit Approval(msg.sender, spender, value);
        return true;
    }

    function transferFrom(address from, address to, uint256 value) external returns (bool) {
        require(balanceOf[from] >= value, "Insufficient balance");
        require(allowance[from][msg.sender] >= value, "Allowance exceeded");
        balanceOf[from] -= value;
        allowance[from][msg.sender] -= value;
        balanceOf[to] += value;
        emit Transfer(from, to, value);
        return true;
    }

    function faucet() external {
        require(block.timestamp - lastFaucetAt[msg.sender] >= FAUCET_COOLDOWN, "Faucet cooldown active");
        lastFaucetAt[msg.sender] = block.timestamp;
        balanceOf[msg.sender] += FAUCET_AMOUNT;
        totalSupply += FAUCET_AMOUNT;
        emit Transfer(address(0), msg.sender, FAUCET_AMOUNT);
    }
}
